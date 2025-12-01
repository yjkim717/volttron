import logging

from device_handlers.base_handler import BaseDeviceHandler

_log = logging.getLogger(__name__)


class SirenHandler(BaseDeviceHandler):
    """
    Siren Handler

        value in {0, 1}  (0 = off, 1 = on)
    """

    def set_state(self, entity_point: str, value: int) -> None:
        """
        entity_point: must be "state"
        value:
          - 0 -> turn_off
          - 1 -> turn_on
        """
        if entity_point != "state":
            _log.warning(
                "SirenHandler: unsupported entity_point '%s'. Only 'state' is supported.",
                entity_point,
            )
            return

        if value not in (0, 1):
            raise ValueError(
                "SirenHandler: 'state' value must be 0 (off) or 1 (on). "
                f"Got: {value!r}"
            )

        service = "turn_on" if value == 1 else "turn_off"

        _log.info(
            "[SIREN] %s → service=%s value=%s",
            self.entity_id,
            service,
            value,
        )

        # Use shared API layer, no direct HTTP here
        self.api.call_service("siren", service, self.entity_id)

    def get_state(self, entity_point: str):
        """
        entity_point == "state" → returns HA state string ("on"/"off")
        entity_point == "<attribute>" → returns HA attribute value, or None
        """
        state_data = self.api.get_state(self.entity_id) or {}

        if entity_point == "state":
            # Home Assistant entity state, e.g. "on"/"off"
            return state_data.get("state")

        # Any other key → look in attributes
        attributes = state_data.get("attributes", {}) or {}
        return attributes.get(entity_point)
