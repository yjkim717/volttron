# -*- coding: utf-8 -*-
import logging
from .base_handler import BaseDeviceHandler

_log = logging.getLogger(__name__)

class LockHandler(BaseDeviceHandler):
    """
    Minimal handler for controlling Home Assistant lock entities.

    This class provides a simple interface for locking and unlocking
    a Home Assistant lock by calling the appropriate HA services.

    Supported operations:
      - lock → lock.lock
      - unlock → lock.unlock

    Example:
        lock = LockHandler(api, "lock.front_door")
        lock.set_state("state", 1)  # Lock
        lock.set_state("state", 0)  # Unlock
    """

    # Unified setter
    def set_state(self, entity_point, value):
        """
        Set the lock state.

        Args:
            entity_point: Typically "state" (for consistency with other handlers)
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
            set_state("state", 1) → calls HA "lock.lock"
            set_state("state", 0) → calls HA "lock.unlock"
        """
        if value not in (0, 1):
            raise ValueError("Lock state must be 0 (unlocked) or 1 (locked).")

        service = "lock" if value == 1 else "unlock"

        _log.info(
            "[LOCK] %s → service=%s value=%s",
            self.entity_id, service, value
        )

        # Use parent class's call_service method
        self.call_service("lock", service)

    def get_state(self, entity_point):
        """
        Returns state of entity, or of a specific entity_point
        
        Args:
            entity_point: "state" or attribute name (e.g., "friendly_name")
        """
        state_data = self.api.get_state(self.entity_id)

        if not state_data:
            return None

        # Lock's "state" = "locked"/"unlocked"
        if entity_point == "state":
            return state_data.get("state")

        # Attributes
        return state_data.get("attributes", {}).get(entity_point)
