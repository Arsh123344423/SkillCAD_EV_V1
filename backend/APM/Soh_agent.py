import json
import os
import concurrent.futures
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from dotenv import load_dotenv
from scipy.optimize import brentq, curve_fit

load_dotenv()

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
#
# The database is resolved straight from the URI itself, e.g. the "mydb" in
#   mongodb+srv://user:pass@cluster.mongodb.net/mydb
# rather than a separate MONGO_DB_NAME env var — one source of truth for
# which DB you're pointed at. MONGO_DB_NAME is kept only as an optional
# fallback for URIs that don't include a database path.

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME")

# ------------------------------------------------------------------
# Mongo Connection Pool
# ------------------------------------------------------------------

mongo_client_instance = None


def get_mongo_client():
    global mongo_client_instance

    if mongo_client_instance is None and MONGO_URI:
        mongo_client_instance = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=1000,
            maxPoolSize=20,
        )

    return mongo_client_instance


def get_database():
    """
    Resolves the database from the connection URI (e.g. the "mydb" in
    "mongodb+srv://user:pass@cluster.mongodb.net/mydb"). Falls back to
    MONGO_DB_NAME only if the URI itself doesn't specify a database.
    """

    client = get_mongo_client()

    if client is None:
        raise RuntimeError(
            "MongoDB client is not configured. Set the MONGO_URI env var."
        )

    try:
        return client.get_default_database(default=MONGO_DB_NAME)

    except ConfigurationError as exc:
        raise RuntimeError(
            "No database name found in MONGO_URI (e.g. '.../mydb') and "
            "MONGO_DB_NAME is not set as a fallback."
        ) from exc


# ------------------------------------------------------------------
# Fetch + Shape Data From Mongo
# ------------------------------------------------------------------
#
# Your documents look like:
# {
#   "soc": 69.42,
#   "voltage": 4.13,
#   "current": -44.91,
#   "battery_temp": 25.45,
#   "ambient_temp": 28,
#   "charging_duration": 0,
#   "charging_cycles": 58,
#   "charging_mode": "Slow",
#   "battery_type": "Li-ion",
#   "ev_model": "Model C",
#   "predicted_degradation": 6.175
# }
#
# There isn't a raw "soh" field, but predicted_degradation gives us one:
#   soh = 100 - predicted_degradation
#
# There will typically be many readings per charging_cycles value (multiple
# telemetry samples taken during the same cycle count), so we group by
# charging_cycles and average the degradation before fitting a curve.


def fetch_battery_data(
    ev_model: Optional[str] = None,
    battery_type: Optional[str] = None,
    collection_name: Optional[str] = None,
) -> Tuple[List[float], List[float]]:
    """
    Pulls telemetry from Mongo and returns (cycles, soh_values), sorted by
    cycle count ascending, with one point per distinct charging_cycles value.
    """

    db = get_database()

    collection_name = collection_name or MONGO_COLLECTION_NAME

    if not collection_name:
        raise ValueError(
            "collection_name must be provided (either as an argument or via "
            "the MONGO_COLLECTION_NAME env var)."
        )

    collection = db[collection_name]

    match_stage: Dict[str, Any] = {}

    if ev_model:
        match_stage["ev_model"] = ev_model

    if battery_type:
        match_stage["battery_type"] = battery_type

    pipeline: List[Dict[str, Any]] = []

    if match_stage:
        pipeline.append({"$match": match_stage})

    pipeline += [
        {
            "$group": {
                "_id": "$charging_cycles",
                "avg_degradation": {"$avg": "$predicted_degradation"},
                "sample_count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    docs = list(collection.aggregate(pipeline))

    if not docs:
        raise ValueError(
            "No matching documents found for the given ev_model/battery_type filters."
        )

    cycles = [float(d["_id"]) for d in docs]
    soh_values = [100.0 - float(d["avg_degradation"]) for d in docs]

    return cycles, soh_values


# ------------------------------------------------------------------
# Degradation Models
# ------------------------------------------------------------------

def power_law(t, a, b, c):
    return 100 - a * (np.asarray(t) ** b) - c


def double_exp(t, a, b, c, d):
    t = np.asarray(t)
    return 100 - a * (1 - np.exp(-b * t)) - c * (1 - np.exp(-d * t))


MODELS = {
    "power_law": {
        "fn": power_law,
        "n_params": 3,
    },
    "double_exp": {
        "fn": double_exp,
        "n_params": 4,
    },
}


# ------------------------------------------------------------------
# Fitting Helpers
# ------------------------------------------------------------------

def _get_initial_guess(cycles_arr, soh_arr, model_name):
    span = max(float(np.max(cycles_arr)), 1.0)
    start_soh = float(np.min(soh_arr))

    if model_name == "power_law":
        return np.array(
            [
                max((100 - start_soh) / (span**1.2), 1e-4),
                1.0,
                max(0, 100 - np.mean(soh_arr[-3:])),
            ]
        )

    return np.array(
        [
            0.001,
            0.001,
            0.001,
            0.0001,
        ]
    )


def _fit_model(cycles_arr, soh_arr, model_name):
    model = MODELS[model_name]

    n_points = len(cycles_arr)
    n_params = model["n_params"]

    if n_points < n_params:
        # Not enough points to fit this model at all - return a degenerate
        # fit rather than letting curve_fit throw a confusing error.
        p0 = _get_initial_guess(cycles_arr, soh_arr, model_name)
        return p0, np.eye(len(p0)) * 1e6

    p0 = _get_initial_guess(
        cycles_arr,
        soh_arr,
        model_name,
    )

    try:
        if model_name == "power_law":

            bounds = (
                [1e-8, 0.1, -100],
                [100, 5.0, 100],
            )

        else:

            bounds = (
                [1e-8, 1e-8, 1e-8, 1e-8],
                [100, 1, 100, 1],
            )

        params, cov = curve_fit(
            model["fn"],
            cycles_arr,
            soh_arr,
            p0=p0,
            bounds=bounds,
            maxfev=5000,
        )

        return params, cov

    except Exception:

        return (
            p0,
            np.eye(len(p0)) * 1e6,
        )


def fit_curve(cycles, soh_values, model_name):
    cycles_arr = np.asarray(cycles, dtype=float)
    soh_arr = np.asarray(soh_values, dtype=float)

    params, cov = _fit_model(
        cycles_arr,
        soh_arr,
        model_name,
    )

    predicted = MODELS[model_name]["fn"](
        cycles_arr,
        *params,
    )

    ss_res = np.sum(
        (soh_arr - predicted) ** 2
    )

    ss_tot = np.sum(
        (soh_arr - np.mean(soh_arr)) ** 2
    )

    r2 = (
        1 - ss_res / ss_tot
        if ss_tot > 0
        else 0
    )

    return {
        "params": params.tolist(),
        "r2": float(r2),
        "param_variance": np.diag(cov).tolist(),
    }


# ------------------------------------------------------------------
# RUL
# ------------------------------------------------------------------

def compute_rul(
    cycles,
    params,
    model_name,
    threshold=80,
    current_cycle=None,
):
    current_cycle = current_cycle or max(cycles)

    model = MODELS[model_name]["fn"]

    def f(t):
        return model(t, *params) - threshold

    try:
        eol_cycle = brentq(
            f,
            current_cycle,
            current_cycle * 10 + 100,
        )

        return {
            "eol_cycle": float(eol_cycle),
            "rul_cycles": float(
                eol_cycle - current_cycle
            ),
        }

    except Exception:

        return {
            "eol_cycle": None,
            "rul_cycles": None,
        }


# ------------------------------------------------------------------
# Backtest
# ------------------------------------------------------------------

def backtest(
    cycles,
    soh_values,
    model_name,
):
    cycles_arr = np.asarray(cycles, dtype=float)
    soh_arr = np.asarray(soh_values, dtype=float)

    split = max(int(len(cycles_arr) * 0.8), MODELS[model_name]["n_params"])
    split = min(split, len(cycles_arr) - 1) if len(cycles_arr) > 1 else len(cycles_arr)

    if split <= 0 or split >= len(cycles_arr):
        # Not enough data to hold out a test split - skip backtesting.
        return {"holdout_mae": None}

    params, _ = _fit_model(
        cycles_arr[:split],
        soh_arr[:split],
        model_name,
    )

    predicted = MODELS[model_name]["fn"](
        cycles_arr[split:],
        *params,
    )

    mae = np.mean(
        np.abs(
            predicted - soh_arr[split:]
        )
    )

    return {
        "holdout_mae": float(mae),
    }


# ------------------------------------------------------------------
# Current SoH
# ------------------------------------------------------------------

def get_current_soh(
    cycles,
    soh_values,
    current_cycle=None,
):
    current_cycle = (
        current_cycle
        if current_cycle is not None
        else max(cycles)
    )

    idx = np.argmin(
        np.abs(
            np.asarray(cycles)
            - current_cycle
        )
    )

    return float(soh_values[idx])


# ------------------------------------------------------------------
# Instant Report
# ------------------------------------------------------------------

def build_local_report(
    fit_results,
    chosen_model,
    backtest_result,
    rul_result,
    current_soh,
    current_cycle,
    cycles_per_day=None,
):

    rul_cycles = rul_result.get(
        "rul_cycles"
    )

    if rul_cycles is None:

        rul_text = "Not reached"

    elif cycles_per_day:

        rul_text = (
            f"{rul_cycles:.0f} cycles "
            f"(~{rul_cycles / cycles_per_day:.1f} days)"
        )

    else:

        rul_text = (
            f"{rul_cycles:.0f} cycles"
        )

    mae = backtest_result.get("holdout_mae")

    return {
        "current_soh_pct": round(
            current_soh,
            2,
        ),
        "current_cycle": current_cycle,
        "selected_model": chosen_model,
        "r2": round(
            fit_results[chosen_model]["r2"],
            4,
        ),
        "mae": round(mae, 3) if mae is not None else None,
        "remaining_useful_life": rul_text,
        "confidence":
            "High near-term confidence. Long-term degradation may vary with usage conditions.",
    }


# ------------------------------------------------------------------
# Main Entry (operates on plain arrays)
# ------------------------------------------------------------------

def run_apm_agent(
    cycles,
    soh_values,
    current_cycle=None,
    cycles_per_day=None,
):

    if len(cycles) != len(soh_values):
        raise ValueError("cycles and soh_values must be the same length.")

    if len(cycles) < 2:
        raise ValueError(
            "Need at least 2 distinct-cycle data points to fit a degradation curve."
        )

    current_cycle = (
        current_cycle
        if current_cycle is not None
        else max(cycles)
    )

    current_soh = get_current_soh(
        cycles,
        soh_values,
        current_cycle,
    )

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        future_power = executor.submit(
            fit_curve,
            cycles,
            soh_values,
            "power_law",
        )

        future_double = executor.submit(
            fit_curve,
            cycles,
            soh_values,
            "double_exp",
        )

        fit_results = {
            "power_law":
                future_power.result(),
            "double_exp":
                future_double.result(),
        }

    if (
        fit_results["double_exp"]["r2"]
        >
        fit_results["power_law"]["r2"]
        + 0.02
    ):
        chosen_model = "double_exp"
    else:
        chosen_model = "power_law"

    backtest_result = backtest(
        cycles,
        soh_values,
        chosen_model,
    )

    rul_result = compute_rul(
        cycles,
        fit_results[chosen_model]["params"],
        chosen_model,
        current_cycle=current_cycle,
    )

    return build_local_report(
        fit_results,
        chosen_model,
        backtest_result,
        rul_result,
        current_soh,
        current_cycle,
        cycles_per_day,
    )


# ------------------------------------------------------------------
# Main Entry (pulls straight from MongoDB)
# ------------------------------------------------------------------

def run_apm_agent_from_db(
    ev_model: Optional[str] = None,
    battery_type: Optional[str] = None,
    collection_name: Optional[str] = None,
    current_cycle: Optional[float] = None,
    cycles_per_day: Optional[float] = None,
):
    """
    End-to-end entry point: fetches telemetry for a given ev_model /
    battery_type from Mongo, then runs the same fitting + RUL pipeline.
    """

    cycles, soh_values = fetch_battery_data(
        ev_model=ev_model,
        battery_type=battery_type,
        collection_name=collection_name,
    )

    return run_apm_agent(
        cycles,
        soh_values,
        current_cycle=current_cycle,
        cycles_per_day=cycles_per_day,
    )


# ------------------------------------------------------------------
# Test / CLI
# ------------------------------------------------------------------

if __name__ == "__main__":

    if MONGO_URI:
        # Real path: read from your backend.
        # Adjust ev_model / battery_type / collection_name as needed.
        report = run_apm_agent_from_db(
            ev_model="Model C",
            battery_type="Li-ion",
            cycles_per_day=3,
        )
    else:
        # Fallback so the script still runs without a DB connection.
        print("MONGO_URI not set - running with synthetic data instead.\n")

        cycles = list(range(0, 500, 5))

        soh_values = [
            100 - 0.02 * (c**1.1)
            + np.random.normal(0, 0.15)
            for c in cycles
        ]

        report = run_apm_agent(
            cycles,
            soh_values,
            cycles_per_day=3,
        )

    print(json.dumps(report, indent=2))