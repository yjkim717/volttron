# -*- coding: utf-8 -*-
import logging

_log = logging.getLogger(__name__)

class LockHandler:
    """
    Minimal handler for controlling Home Assistant lock entities.

    This class provides a simple interface for locking and unlocking
    a Home Assistant lock by calling the appropriate HA services.

    Supported operations:
      - lock → lock.lock
      - unlock → lock.unlock

    Example:
        lock = LockHandler(api, "lock.front_door")
        lock.set_state(1)  # Lock
        lock.set_state(0)  # Unlock
    """

    def __init__(self, api, entity_id):
        """
        Initialize a LockHandler instance.

        Args:
            api: An object that provides a `call_service(domain, service, payload)`
                 method compatible with Home Assistant's service API.
            entity_id (str): The Home Assistant lock entity ID
                 (e.g., "lock.front_door").

        """
        self.api = api
        self.entity_id = entity_id

    def set_state(self, value):
        """
        Set the lock state.

        Args:
            value (int):
                - 1 → lock the entity
                - 0 → unlock the entity

        Raises:
            ValueError: If `value` is not 0 or 1.

        Behavior:
            - Calls Home Assistant `lock.lock` or `lock.unlock`
              depending on the value.
            - Logs the action for debugging.

        Example:
            set_state(1) → calls HA "lock.lock"
            set_state(0) → calls HA "lock.unlock"
        """
        if value not in (0, 1):
            raise ValueError("Lock state must be 0 (unlocked) or 1 (locked).")

        service = "lock" if value == 1 else "unlock"

        _log.info(
            "[LOCK] %s → service=%s value=%s",
            self.entity_id, service, value
        )

        self.api.call_service("lock", service, self.entity_id)