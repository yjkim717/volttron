# -*- coding: utf-8 -*-
import logging

_log = logging.getLogger(__name__)

class FanHandler(BaseDeviceHandler):
    """
    Fan Handler:
    - Supports turning fan on or off via Home Assistant fan.turn_on / fan.turn_off
    - Supports toggling fan oscillation via Home Assitant fan.oscillate
    - Supports adjusting fan speed via Home Assistant fan.set_percentage
    - Supports reading both state & attributes for testing
    """

    def __init__(self, api, entity_id):
        self.api = api
        self.entity_id = entity_id

    # Unified setter
    def set_state(self, entity_point, value):
        """
        entity_point = oscillate, value = 1/0 -> oscillating/not oscillating
        entity_point = power, value = 1/0 -> fan on/fan off
        entity_point = speed, value = 0-100 -> sets fan speed
        """
        if entity_point = "oscillate":
            if value not in (0, 1):
                raise ValueError("Fan oscillation must be 0 (not oscillating) or 1 (oscillating).")
            service = "oscillate"
        
        if entity_point = "power"
            if value not in (0, 1):
                raise ValueError("Fan power must be 0 (off) or 1 (on).")

            if value == 0:
                service = "turn_off"
            else:
                service = "turn_on"
        
        if entity_point = "speed"
            if value not in range(0, 101):
                raise ValueError("Fan speed percentage must be between 0 and 100 inclusive")
            if value == 0:
                service = "turn_off"
            else:
                service = "set_percentage"

        _log.info(
            "[FAN] %s → service=%s value=%s",
            self.entity_id, service, value
        )

        self.api.call_service("fan", service, self.entity_id)

    # get_state for testing
    def get_state(self, entity_point):
        """
        entity_point="properties.oscillating" → returns "true" / "false"
        entity_point="<attribute>" → returns HA attribute value
        """
        state_data = self.api.get_state(self.entity_id)

        # Attributes
        return state_data.get("attributes", {}).get(entity_point)


"""
Example usage 
fan_handler = FanHandler(api, "fan.ceiling")
fan_handler.set_state("power", 1)  # Turns the fan on
fan_handler.set_state("power", 0)  # Turns the fan off
fan_handler.set_state("oscillate", 1)  # Turns fan oscillation on
fan_handler.set_state("oscillate", 0)  # Turns fan oscillation on
fan_handler.set_state("speed", 0) # Sets fan speed to 0%
fan_handler.set_state("speed", 50) # Sets fan speed to 50%
"""