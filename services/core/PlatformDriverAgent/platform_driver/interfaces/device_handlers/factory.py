# -*- coding: utf-8 -*-
"""
HandlerFactory

Factory pattern implementation for creating device handler instances based on entity_id.
This module demonstrates the Dependency Inversion Principle (DIP) by isolating
all concrete handler imports in one place, so that the Home Assistant Interface
does not depend directly on each handler class.

This factory follows several SOLID principles:
- Single Responsibility Principle (SRP): One responsibility - creating handlers
- Open/Closed Principle (OCP): Open for extension (new handlers), closed for modification
- Dependency Inversion Principle (DIP): Depends on abstractions (BaseDeviceHandler)
"""

from __future__ import annotations

from typing import Optional, Type

from .base_handler import BaseDeviceHandler
from .light_handler import LightHandler
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
    Factory class for creating device handler instances based on entity_id.
    
    This class demonstrates the Factory Design Pattern and follows several
    SOLID principles:
    
    - Single Responsibility Principle (SRP): The factory has one responsibility:
      creating the appropriate handler instance based on entity_id prefix.
    
    - Open/Closed Principle (OCP): The factory is open for extension (new handlers
      can be registered) but closed for modification (the core factory logic
      doesn't need to change when adding new handlers).
    
    - Dependency Inversion Principle (DIP): The factory and consumers depend on
      the abstraction (BaseDeviceHandler) rather than concrete implementations.
      This isolates all concrete handler imports in one place.
    
    The factory maintains a registry of entity_id prefixes mapped to handler classes,
    allowing for easy extension and maintenance. It supports both required and
    optional handlers, with appropriate error handling for missing optional handlers.
    
    Attributes:
        _api: The Home Assistant API instance to pass to handlers
        _registry: List of tuples containing (prefix, handler_class, required_flag, name)
    """

    def __init__(self, api):
        """
        Initialize the HandlerFactory with the Home Assistant API instance.
        
        This constructor demonstrates the Dependency Inversion Principle (DIP)
        by accepting the API as a parameter rather than creating it internally.
        This allows for dependency injection and easier testing.
        
        The factory automatically registers all available handlers (both required
        and optional) during initialization, following the Open/Closed Principle
        (OCP) by allowing new handlers to be added without modifying existing code.
        
        Args:
            api: The Home Assistant API instance (or compatible object) to pass
                 to all created handlers
        """
        self._api = api
        self._registry: list[tuple[str, Optional[Type[BaseDeviceHandler]], bool, str]] = []

        # Required handlers - must be available for the system to function
        self._register("light.", LightHandler, required=True, name="LightHandler")
        self._register("climate.", ClimateHandler, required=True, name="ClimateHandler")

        # Optional handlers - may not be available in all installations
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
        Register a handler class for a specific entity_id prefix.
        
        This method demonstrates the Open/Closed Principle (OCP) by providing
        a way to extend the factory's capabilities without modifying its core
        logic. New handlers can be registered by calling this method.
        
        The method follows the Single Responsibility Principle (SRP) by having
        one clear purpose: adding a handler to the registry.
        
        Args:
            prefix (str): The entity_id prefix to match (e.g. "light.", "lock.")
            handler_cls (Optional[Type[BaseDeviceHandler]]): The handler class to use,
                or None if the handler is optional and not available
            required (bool): If True, missing handler_cls is a configuration error.
                           If False, missing handler_cls is acceptable (optional handler)
            name (str): Human-readable handler name for error messages
        
        Note:
            This is a private method intended for internal use during factory
            initialization. External code should not need to call this directly.
        """
        self._registry.append((prefix, handler_cls, required, name))

    def get_handler(self, entity_id: str) -> BaseDeviceHandler:
        """
        Create and return a handler instance for the given entity_id.
        
        This method demonstrates the Factory Design Pattern and follows the
        Dependency Inversion Principle (DIP) by returning a BaseDeviceHandler
        abstraction rather than a concrete implementation.
        
        The method uses a Strategy-like pattern, selecting the appropriate
        handler based on the entity_id prefix. It follows the Single
        Responsibility Principle (SRP) by having one clear purpose: handler
        creation and selection.
        
        Args:
            entity_id (str): The Home Assistant entity ID (e.g., "light.kitchen",
                           "climate.thermostat", "lock.front_door")
        
        Returns:
            BaseDeviceHandler: An instance of the appropriate handler class
                              for the given entity_id
        
        Raises:
            ValueError: If no handler is found for the entity_id prefix, or if
                       a required handler is not available
        
        Example:
            >>> factory = HandlerFactory(api)
            >>> light_handler = factory.get_handler("light.kitchen")
            >>> climate_handler = factory.get_handler("climate.thermostat")
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
