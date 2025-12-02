# -*- coding: utf-8 -*-
"""
SirenHandler

Implements Home Assistant siren control using the shared BaseDeviceHandler
infrastructure. This handler supports a single entity_point ("state") for
turning the siren on or off. All state retrieval is delegated to the unified
HomeAssistantAPI interface.
"""

import logging
from .base_handler import BaseDeviceHandler

_log = logging.getLogger(__name__)


class SirenHandler(BaseDeviceHandler):
    """
    Siren Handler for Home Assistant.

    Responsibilities:
    - Provide unified `set_state()` and `get_state()` methods
      consistent with other device handlers (e.g., LockHandler).
    - Turn the siren ON/OFF using Home Assistant services:
        - siren.turn_on
        - siren.turn_off
    - Retrieve siren state and attributes via `api.get_state(entity_id)`
    """

    # Only "state" is supported for siren devices
    SUPPORTED_POINTS = {"state"}

    def set_state(self, entity_point, value):
        """
        Set the state of the siren.

        Parameters
        ----------
        entity_point : str
            The attribute to set. Only "state" is supported.
        
        value : int
            Expected values:
            - 1 → turn the siren ON  (calls HA service siren.turn_on)
            - 0 → turn the siren OFF (calls HA service siren.turn_off)

        Raises
        ------
        ValueError
            If entity_point is unsupported or value is not 0/1.

        Behavior
        --------
        Uses BaseDeviceHandler.call_service():
            self.call_service(domain, service, extra)
        This delegates to HomeAssistantAPI.call_service() internally.
        """
        # Validate supported attribute
        if entity_point not in self.SUPPORTED_POINTS:
            raise ValueError(
                f"Unsupported entity_point '{entity_point}' for SirenHandler. "
                f"Supported: {self.SUPPORTED_POINTS}"
            )

        # Validate acceptable values
        if value not in (0, 1):
            raise ValueError("Siren 'state' must be 0 (off) or 1 (on).")

        # Map numeric value to HA service name
        service = "turn_on" if value == 1 else "turn_off"

        _log.info(
            "[SIREN] %s → service=%s (value=%s)",
            self.entity_id,
            service,
            value,
        )

        # Call HA service using the BaseDeviceHandler helper
        # Note: extra=None because siren turn_on/off typically only needs entity_id
        self.call_service("siren", service)

    def get_state(self, entity_point):
        """
        Retrieve siren state or attribute.

        Parameters
        ----------
        entity_point : str
            - "state"   → returns top-level HA entity state ("on" / "off")
            - otherwise → attempts to return an attribute under `attributes`

        Returns
        -------
        Any
            - "on"/"off" for state
            - Attribute value, if available
            - None if unavailable or if entity is missing

        Behavior
        --------
        The method queries the Home Assistant state machine via:
            self.api.get_state(self.entity_id)

        Example returned structure:
            {
                "state": "on",
                "attributes": {
                    "volume_level": 0.5,
                    "friendly_name": "My Siren"
                }
            }
        """
        state_data = self.api.get_state(self.entity_id)

        # If HA returned no state (device offline / not found)
        if not state_data:
            return None

        # Handle the main state ("on" / "off")
        if entity_point == "state":
            return state_data.get("state")

        # Fallback: return attributes
        return state_data.get("attributes", {}).get(entity_point)
