
import time
from gradio_client import Client
from APM.simulator import EV, model_input_from_telemetry
import os


HF_SPACE = os.getenv("HF_SPACE")  
API_NAME = os.getenv("HF_API_NAME")  
client = Client(HF_SPACE)


def get_prediction(telemetry: dict) -> str:
    model_input = model_input_from_telemetry(telemetry)
    result = client.predict(
        model_input["SOC (%)"],
        model_input["Voltage (V)"],
        model_input["Current (A)"],
        model_input["Battery Temp (°C)"],
        model_input["Ambient Temp (°C)"],
        model_input["Charging Duration (min)"],
        model_input["Charging Cycles"],
        model_input["Charging Mode"],
        model_input["Battery Type"],
        model_input["EV Model"],
        api_name=API_NAME,
    )
    return result


if __name__ == "__main__":
    fleet_size = 5
    fleet = [EV(f"EV_{i:03}") for i in range(1, fleet_size + 1)]

    while True:
        for vehicle in fleet:
            telemetry = vehicle.update()
            prediction = get_prediction(telemetry)
            print(f"{telemetry['vehicle_id']} | SOC={telemetry['SOC (%)']:.1f}% | "
                  f"Charging={telemetry['charging']} | Predicted degradation: {prediction}")
        time.sleep(1)