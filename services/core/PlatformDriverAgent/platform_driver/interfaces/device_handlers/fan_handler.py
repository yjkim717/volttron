# -*- coding: utf-8 -*-
import logging
from .base_handler import BaseDeviceHandler
from typing import Dict, Tuple, Callable

_log = logging.getLogger(__name__)


class FanHandler(BaseDeviceHandler):
    """
    Fan Handler:
    - Supports turning fan on or off via Home Assistant fan.turn_on / fan.turn_off
    - Supports toggling fan oscillation via Home Assistant fan.oscillate
    - Supports adjusting fan speed via Home Assistant fan.set_percentage
    - Supports reading both state & attributes for testing

    Example usage 
    fan_handler = FanHandler(api, "fan.ceiling")
    fan_handler.set_state("power", 1)  # Turns the fan on
    fan_handler.set_state("power", 0)  # Turns the fan off
    fan_handler.set_state("oscillate", 1)  # Turns fan oscillation on
    fan_handler.set_state("oscillate", 0)  # Turns fan oscillation on
    fan_handler.set_state("speed", 0) # Sets fan speed to 0%
    fan_handler.set_state("speed", 50) # Sets fan speed to 50%
    """

    def __init__(self, api, entity_id):
        """ 
        Initialize a fan handler with dictionary mapping entity_points to respective
        methods
        
        Args: 
            api: HA API
            entity_id: entity ID of fan to be controlled
        """
        super().__init__(api, entity_id)
        # Registry pattern: Map entity_point to handler method
        self._state_handlers: Dict[str, Callable[[int], Tuple[str, dict]]] = {
            "oscillate": self._handle_oscillate,
            "power": self._handle_power,
            "speed": self._handle_speed,
        }

    def set_state(self, entity_point: str, value: int) -> None:
        """
        Unified setter using Strategy pattern.
        
        Args:
            entity_point: "oscillate", "power", or "speed"
            value: 
                - oscillate: 0 (off) or 1 (on)
                - power: 0 (off) or 1 (on)
                - speed: 0-100 (percentage)
        """
        # Strategy pattern: Look up handler from registry
        handler = self._state_handlers.get(entity_point)
        if handler is None:
            raise ValueError(
                f"Unsupported entity_point '{entity_point}' for FanHandler. "
                f"Supported: {list(self._state_handlers.keys())}"
            )

        # Delegate to specific handler strategy
        service, payload = handler(value)
        
        _log.info(
            "[FAN] %s → service=%s value=%s",
            self.entity_id, service, value
        )

        # Call HA service
        self.api.call_service("fan", service, payload)

    # Strategy methods: Each entity_point has its own set handler
    def _handle_oscillate(self, value: int) -> Tuple[str, dict]:
        #Strategy for handling oscillate entity_point
        if value not in (0, 1):
            raise ValueError(
                "Fan oscillation must be 0 (not oscillating) or 1 (oscillating)."
            )
        return "oscillate", {
            "entity_id": self.entity_id,
            "oscillating": bool(value)
        }

    def _handle_power(self, value: int) -> Tuple[str, dict]:
        #Strategy for handling power entity_point
        if value not in (0, 1):
            raise ValueError("Fan power must be 0 (off) or 1 (on).")

        service = "turn_off" if value == 0 else "turn_on"
        return service, {"entity_id": self.entity_id}

    def _handle_speed(self, value: int) -> Tuple[str, dict]:
        #Strategy for handling speed entity_point
        if not (0 <= value <= 100):
            raise ValueError(
                "Fan speed percentage must be between 0 and 100 inclusive"
            )

        if value == 0:
            # Home Assistant convention: 0% = turn_off
            return "turn_off", {"entity_id": self.entity_id}
        else:
            return "set_percentage", {
                "entity_id": self.entity_id,
                "percentage": value
            }

    # get_state for testing
    def get_state(self, entity_point):
        """
        Returns state of entity, or of a specific entity_point
        
        Args:
            entity_point: "state", "oscillate", "power", or "speed"
            Where "state" and "power" have the same meaning
        """
        state_data = self.api.get_state(self.entity_id)

        # Fan's "state" = "on"/"off"
        if entity_point == "state":
            return state_data.get("state")

        # Attributes
        return state_data.get("attributes", {}).get(entity_point)
