# device_handlers/handler_factory.py

from .light_handler import LightHandler
from .switch_handler import SwitchHandler
from .climate_handler import ClimateHandler
from .fan_handler import FanHandler
from .lock_handler import LockHandler
from .siren_handler import SirenHandler
from .input_boolean_handler import InputBooleanHandler


class HandlerFactory:
    """
    Strategy + Factory Pattern
    Maps Home Assistant entity domain → proper Handler class
    """

    HANDLER_MAP = {
        "light": LightHandler,
        "switch": SwitchHandler,
        "climate": ClimateHandler,
        "fan": FanHandler,
        "lock": LockHandler,
        "siren": SirenHandler,
        "input_boolean": InputBooleanHandler,
    }

    @classmethod
    def get_handler(cls, api, entity_id):
        domain = entity_id.split(".")[0]

        handler_cls = cls.HANDLER_MAP.get(domain)
        if handler_cls is None:
            raise ValueError(f"Unsupported entity type: {domain}")

        return handler_cls(api, entity_id)
