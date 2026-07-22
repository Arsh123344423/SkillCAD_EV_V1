import time
import requests

from APM.simulator import EV, model_input_from_telemetry

API_URL = "http://localhost:8000/predict"


def get_prediction(telemetry):

    model_input = model_input_from_telemetry(telemetry)

    payload = {
        "soc": model_input["SOC (%)"],
        "voltage": model_input["Voltage (V)"],
        "current": model_input["Current (A)"],
        "battery_temp": model_input["Battery Temp (°C)"],
        "ambient_temp": model_input["Ambient Temp (°C)"],
        "charging_duration": model_input["Charging Duration (min)"],
        "charging_cycles": model_input["Charging Cycles"],
        "charging_mode": model_input["Charging Mode"],
        "battery_type": model_input["Battery Type"],
        "ev_model": model_input["EV Model"]
    }

    response = requests.post(API_URL, json=payload)
    print("STATUS:", response.status_code) 
    print("RAW RESPONSE:", response.text) 
    payload["predicted_degradation"] = response.json().get("predicted_degradation", None)

    return payload


if __name__ == "__main__":

    fleet_size = 1
    fleet = [EV()]

    while True:

        for vehicle in fleet:

            telemetry = vehicle.update()

            prediction = get_prediction(telemetry)

            print(
                f"{telemetry['vehicle_id']} | "
                f"SOC={telemetry['SOC (%)']:.1f}% | "
                f"Predicted Degradation={prediction}"
            )

        time.sleep(1)