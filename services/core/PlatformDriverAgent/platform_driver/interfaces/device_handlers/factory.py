# -*- coding: utf-8 -*-
"""
HandlerFactory

Given an entity_id, returns the appropriate device handler instance.
This isolates all concrete handler imports in one place, so that the
Home Assistant Interface does not depend directly on each handler class.
"""

from __future__ import annotations

from typing import Optional, Type

from .base_handler import BaseDeviceHandler
from .light_handler import LightHandler
from .switch_handler import SwitchHandler
from .climate_handler import ClimateHandler

# Optional handlers
try:
    from .lock_handler import LockHandler
except ImportError:  # pragma: no cover - optional
    LockHandler = None  # type: ignore[assignment]

try:
    from .fan_handler import FanHandler
except ImportError:  # pragma: no cover - optional
    FanHandler = None  # type: ignore[assignment]

try:
    from .siren_handler import SirenHandler
except ImportError:  # pragma: no cover - optional
    SirenHandler = None  # type: ignore[assignment]


class HandlerFactory:
    """
    Factory/Strategy for resolving entity_id -> concrete handler.

    - Keeps a registry of (prefix, handler_cls, required_flag)
    - Only this module imports concrete handlers
    - Home Assistant interface depends only on HandlerFactory + BaseDeviceHandler
      (DIP: depends on abstraction, not implementations)
    """

    def __init__(self, api):
        self._api = api
        self._registry: list[tuple[str, Optional[Type[BaseDeviceHandler]], bool, str]] = []

        # Required handlers
        self._register("light.", LightHandler, required=True, name="LightHandler")
        self._register("switch.", SwitchHandler, required=True, name="SwitchHandler")
        self._register("climate.", ClimateHandler, required=True, name="ClimateHandler")

        # Optional handlers
        self._register("lock.", LockHandler, required=False, name="LockHandler")
        self._register("fan.", FanHandler, required=False, name="FanHandler")
        self._register("siren.", SirenHandler, required=False, name="SirenHandler")

    def _register(
        self,
        prefix: str,
        handler_cls: Optional[Type[BaseDeviceHandler]],
        required: bool,
        name: str,
    ) -> None:
        """
        :param prefix: entity_id prefix, e.g. "light.", "lock.", …
        :param handler_cls: handler class or None (if optional & not installed)
        :param required: if True, missing handler_cls is configuration error
        :param name: human-readable handler name for error messages
        """
        self._registry.append((prefix, handler_cls, required, name))

    def get_handler(self, entity_id: str) -> BaseDeviceHandler:
        """
        Return a handler instance for the given entity_id, or raise
        ValueError if unsupported or missing.
        """
        for prefix, handler_cls, required, name in self._registry:
            if not entity_id.startswith(prefix):
                continue

            if handler_cls is None:
                if required:
                    raise ValueError(
                        f"{name} is required but not available for entity_id '{entity_id}'."
                    )
                raise ValueError(
                    f"Optional handler {name} is not available for entity_id '{entity_id}'."
                )

            return handler_cls(self._api, entity_id)

        # No prefix matched
        raise ValueError(f"Unsupported entity type for entity_id: {entity_id}")
