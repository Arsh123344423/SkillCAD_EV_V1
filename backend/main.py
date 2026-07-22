from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import os

from APM.Multi_agent_steup import run_coordinator_agent
from APM.Soh_agent import (
    MONGO_COLLECTION_NAME,
    run_apm_agent,
    run_apm_agent_from_db,
)

# Import Track B functions cleanly
from SCM.track_b_agent import (
    run_supply_chain_agent,
    analyze_supplier_risk,
    get_graph_visualization_data,
)

router = APIRouter()

app = FastAPI(title="SkillCAD EV Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BatteryAnalysisDBRequest(BaseModel):
    """Analyze a battery by pulling its telemetry straight from MongoDB."""
    ev_model: Optional[str] = Field(None, description="e.g. 'Model C'")
    battery_type: Optional[str] = Field(None, description="e.g. 'Li-ion'")
    current_cycle: Optional[float] = None
    cycles_per_day: Optional[float] = None


class CoordinatorRequest(BaseModel):
    query: str
    asset_id: Optional[str] = None


class SupplyChainNodeRequest(BaseModel):
    supplier_id: str = Field(..., description="e.g. 'India_ACC_Gigafactories'")


class SupplyChainAgentRequest(BaseModel):
    query: str = Field(..., description="Query for India Supply Chain Agent")

# Endpoints for the SkillCAD EV Backend API.

@app.get("/")
def health_check():
    return {"status": "ok", "service": "SkillCAD EV Backend"}

# Track A: APM Agent Endpoints
@app.post("/analyze/db")
def analyze_battery_from_db(req: BatteryAnalysisDBRequest):
    """Fetch telemetry from MongoDB for the given ev_model/battery_type and analyze it."""
    try:
        report = run_apm_agent_from_db(
            ev_model=req.ev_model,
            battery_type=req.battery_type,
            collection_name=MONGO_COLLECTION_NAME,
            current_cycle=req.current_cycle,
            cycles_per_day=req.cycles_per_day,
        )
        return report

    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/agents/coordinator")
def coordinator(req: CoordinatorRequest):
    try:
        result = run_coordinator_agent(req.query, asset_id=req.asset_id)
        return {
            "agent": result.get("agent"),
            "response": result.get("response", "No response generated."),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# TRACK B: SUPPLY CHAIN ENDPOINTS
@app.get("/supply-chain/nodes")
def get_supply_chain_nodes():
    """Returns nodes and edges for UI visualization."""
    return get_graph_visualization_data()


@app.post("/supply-chain/analyze-node")
def analyze_node_risk(req: SupplyChainNodeRequest):
    """Returns calculated local and propagated risk for a single supplier node."""
    res = analyze_supplier_risk(req.supplier_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@app.post("/supply-chain/agent")
def run_track_b_agent_endpoint(req: SupplyChainAgentRequest):
    """Triggers the Track B Gemini Agent via run_supply_chain_agent()."""
    try:
        response_text = run_supply_chain_agent(req.query)
        return {
            "query": req.query,
            "agent": "India_Supply_Chain_Agent",
            "analysis": response_text
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err)) from val_err
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)