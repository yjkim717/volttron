# -*- coding: utf-8 -*-
import logging

_log = logging.getLogger(__name__)

class LockHandler:
    """
    Minimal Lock Handler:
    - Supports locked/unlocked via Home Assistant lock.lock / lock.unlock
    - Supports reading both state & attributes for testing
    """

    def __init__(self, api, entity_id):
        self.api = api
        self.entity_id = entity_id

    # Unified setter
    def set_state(self, value):
        """
        value = 1 → locked
        value = 0 → unlocked
        """
        if value not in (0, 1):
            raise ValueError("Lock state must be 0 (unlocked) or 1 (locked).")

        service = "lock" if value == 1 else "unlock"

        _log.info(
            "[LOCK] %s → service=%s value=%s",
            self.entity_id, service, value
        )

        self.api.call_service("lock", service, self.entity_id)
    
    # Minimal get_state for testing
    def get_state(self, entity_point):
        """
        entity_point="state" → returns "locked" / "unlocked"
        entity_point="<attribute>" → returns HA attribute value
        """
        state_data = self.api.get_state(self.entity_id)

        if entity_point == "state":
            return state_data.get("state")  # "locked" or "unlocked"

        # Attributes
        return state_data.get("attributes", {}).get(entity_point)


"""
Example usage 

lock_handler = LockHandler(api, "lock.front_door")
lock_handler.set_state(1)  # Locks the door
lock_handler.set_state(0)  # Unlocks the door
"""