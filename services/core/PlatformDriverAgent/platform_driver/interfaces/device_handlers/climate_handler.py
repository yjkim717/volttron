# services/core/PlatformDriverAgent/platform_driver/interfaces/device_handlers/climate_handler.py
# -*- coding: utf-8 -*-

import logging
from .base_handler import BaseDeviceHandler

_log = logging.getLogger(__name__)


class ClimateHandler(BaseDeviceHandler):
    """
    Climate Handler for Home Assistant:
    - Supports hvac_mode (heat/cool/off)
    - Supports setting target temperature
    - Implements unified set_state(entity_point, value)
    - Supports get_state(entity_point)
    """

    SUPPORTED_POINTS = {"temperature", "hvac_mode", "state"}

    def set_state(self, entity_point, value):
        """
        entity_point:
            - "temperature" (numeric)
            - "hvac_mode" (string: "heat", "cool", "off")
            - "state" → alias for "hvac_mode"

        value:
            - temperature: number
            - hvac_mode: string
        """
        if entity_point not in self.SUPPORTED_POINTS:
            raise ValueError(f"Unsupported climate attribute: {entity_point}")

        if entity_point == "temperature":
            service = "set_temperature"
            data = {"entity_id": self.entity_id, "temperature": value}

        elif entity_point in ("hvac_mode", "state"):
            service = "set_hvac_mode"
            data = {"entity_id": self.entity_id, "hvac_mode": value}

        else:
            raise ValueError(f"Invalid entity_point: {entity_point}")

        _log.info(f"[CLIMATE] {self.entity_id} → {entity_point} = {value}")

        self.api.call_service("climate", service, data)

    def get_state(self, entity_point):
        """
        entity_point = "state" or attribute name:
        - "state" returns hvac_mode ("heat","cool","off")
        - "temperature" returns attributes["temperature"]
        - any other attribute returns attributes.get(entity_point)
        """

        state_data = self.api.get_state(self.entity_id)

        if not state_data:
            return None

        if entity_point == "state":
            return state_data.get("state")

        return state_data.get("attributes", {}).get(entity_point)
