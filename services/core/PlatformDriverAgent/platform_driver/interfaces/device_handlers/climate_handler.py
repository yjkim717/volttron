# device_handlers/climate_handler.py
import requests
import logging
from device_handlers.base_handler import BaseDeviceHandler

_log = logging.getLogger(__name__)

class ClimateHandler(BaseDeviceHandler):
    def set_state(self, entity_point, value):
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

        if entity_point == "state":
            mode_map = {0: "off", 2: "heat", 3: "cool", 4: "auto"}
            mode = mode_map.get(value, "off")
            url = f"http://{self.ip}:{self.port}/api/services/climate/set_hvac_mode"
            payload = {"entity_id": self.entity_id, "hvac_mode": mode}
        elif entity_point == "temperature":
            url = f"http://{self.ip}:{self.port}/api/services/climate/set_temperature"
            payload = {"entity_id": self.entity_id, "temperature": value}
        else:
            raise ValueError(f"Unsupported climate attribute: {entity_point}")

        response = requests.post(url, headers=headers, json=payload)
        _log.info(f"Climate {self.entity_id} → {entity_point}={value} ({response.status_code})")

    def get_state(self):
        url = f"http://{self.ip}:{self.port}/api/states/{self.entity_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.get(url, headers=headers)
        return resp.json() if resp.status_code == 200 else None
