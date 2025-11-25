# -*- coding: utf-8 -*-
"""
BaseDeviceHandler

Abstract base class for all Home Assistant device handlers.
Each concrete handler (light, climate, fan, lock, siren, …)
should extend this class and implement `set_state`.
"""

from __future__ import annotations

import abc
from typing import Any


class BaseDeviceHandler(abc.ABC):
    """
    Base class for Home Assistant device handlers.

    Common responsibilities:
    - Hold shared HomeAssistantAPI instance
    - Hold entity_id (e.g., "light.living_room")
    - Optionally provide helper to call HA services
    """

    def __init__(self, api, entity_id: str):
        """
        :param api: HomeAssistantAPI (or compatible object with call_service)
        :param entity_id: Home Assistant entity_id (e.g. "light.kitchen")
        """
        self._api = api
        self._entity_id = entity_id

    @property
    def entity_id(self) -> str:
        return self._entity_id

    @property
    def api(self):
        """
        Expose underlying API (HomeAssistantAPI) to subclasses.
        """
        return self._api

    def call_service(self, domain: str, service: str, extra: dict | None = None) -> Any:
        """
        Convenience wrapper around api.call_service.
        Most device handlers will use this instead of manually
        constructing URLs or headers.
        """
        return self._api.call_service(domain, service, self._entity_id, extra=extra)

    @abc.abstractmethod
    def set_state(self, entity_point: str, value: Any) -> None:
        """
        Set the device state for a specific attribute (entity_point),
        e.g. "state", "brightness", "temperature", …

        Implemented by each concrete handler.
        """
        raise NotImplementedError
