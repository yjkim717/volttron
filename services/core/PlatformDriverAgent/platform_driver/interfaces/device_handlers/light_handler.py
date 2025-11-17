# device_handlers/light_handler.py
import requests
import logging
from device_handlers.base_handler import BaseDeviceHandler

_log = logging.getLogger(__name__)

class LightHandler(BaseDeviceHandler):
    def set_state(self, entity_point, value):
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

        if entity_point == "state":
            service = "turn_on" if value == 1 else "turn_off"
            url = f"http://{self.ip}:{self.port}/api/services/light/{service}"
            payload = {"entity_id": self.entity_id}
        elif entity_point == "brightness":
            url = f"http://{self.ip}:{self.port}/api/services/light/turn_on"
            payload = {"entity_id": self.entity_id, "brightness": value}
        else:
            raise ValueError(f"Unsupported light attribute: {entity_point}")

        response = requests.post(url, headers=headers, json=payload)
        _log.info(f"Light {self.entity_id} → {entity_point}={value} ({response.status_code})")

    def get_state(self):
        url = f"http://{self.ip}:{self.port}/api/states/{self.entity_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.get(url, headers=headers)
        return resp.json() if resp.status_code == 200 else None
