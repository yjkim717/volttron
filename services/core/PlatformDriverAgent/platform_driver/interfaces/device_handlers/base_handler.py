# device_handlers/base_handler.py
from abc import ABC, abstractmethod

class BaseDeviceHandler(ABC):
    """Abstract base class for all Home Assistant device handlers."""

    def __init__(self, ip, port, token, entity_id):
        self.ip = ip
        self.port = port
        self.token = token
        self.entity_id = entity_id

    @abstractmethod
    def set_state(self, entity_point, value):
        """Set the state/value of a device entity."""
        pass

    @abstractmethod
    def get_state(self):
        """Fetch the current state/value of a device entity."""
        pass
