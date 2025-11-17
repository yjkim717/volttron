# device_handlers/switch_handler.py
import requests
import logging
from device_handlers.base_handler import BaseDeviceHandler

_log = logging.getLogger(__name__)

class SwitchHandler(BaseDeviceHandler):
    def set_state(self, entity_point, value):
        if entity_point != "state":
            _log.warning(f"Switch supports only 'state' attribute.")
            return

        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        service = "turn_on" if value == 1 else "turn_off"
        url = f"http://{self.ip}:{self.port}/api/services/switch/{service}"
        payload = {"entity_id": self.entity_id}

        response = requests.post(url, headers=headers, json=payload)
        _log.info(f"Switch {self.entity_id} → {service} ({response.status_code})")

    def get_state(self):
        url = f"http://{self.ip}:{self.port}/api/states/{self.entity_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.get(url, headers=headers)
        return resp.json() if resp.status_code == 200 else None
