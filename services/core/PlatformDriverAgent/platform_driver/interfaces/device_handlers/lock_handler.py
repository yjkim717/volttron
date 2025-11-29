# -*- coding: utf-8 -*-
import logging

_log = logging.getLogger(__name__)

class LockHandler:
    """
    Minimal Lock Handler:
    - Supports locked/unlocked via Home Assistant lock.lock / lock.unlock
    """

    def __init__(self, api, entity_id):
        self.api = api
        self.entity_id = entity_id

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

"""
Example usage 

lock_handler = LockHandler(api, "lock.front_door")
lock_handler.set_state(1)  # Locks the door
lock_handler.set_state(0)  # Unlocks the door
"""