import random
import time
import json
from datetime import datetime

CHARGING_MODES = ["Fast", "Normal", "Slow"]
BATTERY_TYPES = ["Li-ion", "LiFePO4"]
EV_MODELS = ["Model A", "Model B", "Model C"]


class EV:
    def __init__(self):
        self.vehicle_id = "EV_001"
        self.soc = random.uniform(60, 90)
        self.soh = random.uniform(95, 100)
        self.battery_temp = random.uniform(25, 35)
        self.ambient_temp = 28.0
        self.voltage = random.uniform(3.8, 4.2)
        self.current = 0.0
        self.speed = 0.0
        self.odometer = random.randint(1000, 50000)
        self.charge_cycles = random.randint(50, 1000)
        self.fast_charge_count = random.randint(0, 200)
        self.charging = False

        # fixed per-vehicle identity fields the model needs
        self.battery_type = random.choice(BATTERY_TYPES)
        self.ev_model = random.choice(EV_MODELS)

        # state for fixing the charge_cycles bug + tracking session duration
        self._was_full = False
        self._charging_duration_steps = 0  # steps (~1s each) in the CURRENT charging session

    def update(self):
        # switch between charging and driving
        if random.random() < 0.05:
            self.charging = not self.charging
            if self.charging:
                self._charging_duration_steps = 0  # new session starts fresh

        if self.charging:
            self.speed = 0
            self.current = random.uniform(40, 150)
            self.soc += random.uniform(0.05, 0.2)
            self.battery_temp += random.uniform(0.01, 0.08)
            self._charging_duration_steps += 1
        else:
            self.speed = random.uniform(20, 100)
            self.current = random.uniform(-120, -20)
            self.soc -= random.uniform(0.02, 0.08)
            self.battery_temp += abs(self.current) * 0.0008
            self.odometer += self.speed / 3600
            self._charging_duration_steps = 0  # not charging -> no active session

        # natural cooling
        if self.battery_temp > self.ambient_temp:
            self.battery_temp -= 0.03

        # degradation (flat baseline drift)
        self.soh -= 0.00001

        # cycle increment — FIXED: only count the transition into "full",
        # not every step while soc happens to stay >= 99
        if self.soc >= 99 and not self._was_full:
            self.charge_cycles += 1
            self._was_full = True
        elif self.soc < 95:
            self._was_full = False

        # limits
        self.soc = max(0, min(100, self.soc))
        self.soh = max(70, min(100, self.soh))
        self.battery_temp = max(20, min(65, self.battery_temp))

        # thermal anomaly
        thermal_alert = False
        if random.random() < 0.001:
            self.battery_temp += random.uniform(8, 15)
            thermal_alert = True

        if self.charging:
            if self.current >= 110:
                charging_mode = "Fast"
                if self._charging_duration_steps == 1:  # count once, at session start
                    self.fast_charge_count += 1
            elif self.current >= 70:
                charging_mode = "Normal"
            else:
                charging_mode = "Slow"
        else:
            charging_mode = "Slow"

        charging_duration_min = round(self._charging_duration_steps / 60, 3)  # ~1s/step -> minutes

        return {
            # --- identity / context (not model inputs, kept for fleet monitoring) ---
            "vehicle_id": self.vehicle_id,
            "timestamp": datetime.utcnow().isoformat(),
            "speed": round(self.speed, 2),
            "odometer": round(self.odometer, 2),
            "soh": round(self.soh, 2),
            "fast_charge_count": self.fast_charge_count,
            "charging": self.charging,
            "thermal_alert": thermal_alert,

            # --- exact fields expected by the trained model ---
            "SOC (%)": round(self.soc, 2),
            "Voltage (V)": round(self.voltage, 2),
            "Current (A)": round(self.current, 2),
            "Battery Temp (°C)": round(self.battery_temp, 2),
            "Ambient Temp (°C)": round(self.ambient_temp, 2),
            "Charging Duration (min)": charging_duration_min,
            "Charging Cycles": self.charge_cycles,
            "Charging Mode": charging_mode,
            "Battery Type": self.battery_type,
            "EV Model": self.ev_model,
        }


def model_input_from_telemetry(telemetry: dict) -> dict:
    """Extract exactly the fields the trained model expects, in one place,
    so the simulator's extra monitoring fields never leak into a prediction call."""
    return {
        "SOC (%)": telemetry["SOC (%)"],
        "Voltage (V)": telemetry["Voltage (V)"],
        "Current (A)": telemetry["Current (A)"],
        "Battery Temp (°C)": telemetry["Battery Temp (°C)"],
        "Ambient Temp (°C)": telemetry["Ambient Temp (°C)"],
        "Charging Duration (min)": telemetry["Charging Duration (min)"],
        "Charging Cycles": telemetry["Charging Cycles"],
        "Charging Mode": telemetry["Charging Mode"],
        "Battery Type": telemetry["Battery Type"],
        "EV Model": telemetry["EV Model"],
    }


if __name__ == "__main__":
    fleet_size = 10
    fleet = [EV(f"EV_{i:03}") for i in range(1, fleet_size + 1)]

    while True:
        for vehicle in fleet:
            telemetry = vehicle.update()
            print(json.dumps(telemetry))
        time.sleep(2058)