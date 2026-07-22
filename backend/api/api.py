from fastapi import FastAPI, HTTPException
import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from pydantic import BaseModel

app = FastAPI(title="EV Degradation Predictor")

# --- Load preprocessor (scaler + one-hot encoder) ---
preprocess = joblib.load("../models/degradation_model.joblib")  # this is the ColumnTransformer, not a full model


# --- Define the same architecture used during training ---
class DegradationNN(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.net(x)


# --- Load the trained neural network weights ---
checkpoint = torch.load("../models/degradation_nn.pt", map_location="cpu", weights_only=False)
model = DegradationNN(checkpoint["n_features"])
model.load_state_dict(checkpoint["state_dict"])
model.eval()


class Telemetry(BaseModel):
    soc: float
    voltage: float
    current: float
    battery_temp: float
    ambient_temp: float
    charging_duration: float
    charging_cycles: int
    charging_mode: str
    battery_type: str
    ev_model: str


@app.get("/")
def home():
    return {"status": "running"}


@app.post("/predict")
def predict(data: Telemetry):
    try:
        row = pd.DataFrame([{
            "SOC (%)": data.soc,
            "Voltage (V)": data.voltage,
            "Current (A)": data.current,
            "Battery Temp (°C)": data.battery_temp,
            "Ambient Temp (°C)": data.ambient_temp,
            "Charging Duration (min)": data.charging_duration,
            "Charging Cycles": data.charging_cycles,
            "Charging Mode": data.charging_mode,
            "Battery Type": data.battery_type,
            "EV Model": data.ev_model,
        }])

        X = preprocess.transform(row).astype(np.float32)
        with torch.no_grad():
            prediction = model(torch.tensor(X)).item()

        return {"predicted_degradation": round(prediction, 3)}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))