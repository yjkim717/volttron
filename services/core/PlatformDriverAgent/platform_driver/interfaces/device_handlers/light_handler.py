# -*- coding: utf-8 -*-
import logging

_log = logging.getLogger(__name__)


class LightHandler:
    """
    Minimal Light Handler:
    - Supports on/off via Home Assistant light.turn_on / light.turn_off
    """

    def __init__(self, api, entity_id):
        self.api = api
        self.entity_id = entity_id

    def set_state(self, entity_point, value):
        """
        entity_point will normally be "state"
        value = 1 → turn_on
        value = 0 → turn_off
        """
        if value not in (0, 1):
            raise ValueError("Light state must be 0 (off) or 1 (on).")

        service = "turn_on" if value == 1 else "turn_off"

        _log.info(
            "[LIGHT] %s → service=%s value=%s",
            self.entity_id, service, value
        )

        self.api.call_service("light", service, self.entity_id)
