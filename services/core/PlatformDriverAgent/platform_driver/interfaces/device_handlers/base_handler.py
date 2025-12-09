# -*- coding: utf-8 -*-
"""
BaseDeviceHandler

Abstract base class for all Home Assistant device handlers.
Each concrete handler (light, climate, fan, lock, siren, …)
should extend this class and implement `set_state`.

This module demonstrates several SOLID principles:
- Single Responsibility Principle (SRP): Each handler has one responsibility
- Open/Closed Principle (OCP): Open for extension via inheritance, closed for modification
- Liskov Substitution Principle (LSP): All handlers can be used interchangeably
- Dependency Inversion Principle (DIP): Depends on abstractions (abc.ABC)
"""

from __future__ import annotations

import abc
from typing import Any


class BaseDeviceHandler(abc.ABC):
    """
    Abstract base class for all Home Assistant device handlers.
    
    This class demonstrates the Open/Closed Principle (OCP) by providing
    a stable base interface that is open for extension through inheritance
    but closed for modification. New device types can be added by creating
    new subclasses without modifying this base class.
    
    The class also follows the Dependency Inversion Principle (DIP) by
    depending on abstractions (the API interface) rather than concrete
    implementations. This allows for easy testing and mocking.
    
    All concrete handlers must implement the abstract set_state() method,
    ensuring they follow the Liskov Substitution Principle (LSP) - any
    handler can be used wherever a BaseDeviceHandler is expected.

    Common responsibilities:
    - Hold shared HomeAssistantAPI instance
    - Hold entity_id (e.g., "light.living_room")
    - Optionally provide helper to call HA services
    
    Attributes:
        _api: The Home Assistant API instance (or compatible object)
        _entity_id: The Home Assistant entity ID (e.g., "light.kitchen")
    """

    def __init__(self, api, entity_id: str):
        """
        Initialize the base device handler.
        
        This constructor follows the Dependency Inversion Principle (DIP)
        by accepting an API object rather than creating one internally.
        This allows for dependency injection and easier testing.
        
        Args:
            api: HomeAssistantAPI (or compatible object with call_service method)
            entity_id (str): Home Assistant entity_id (e.g. "light.kitchen")
            
        Note:
            The api parameter accepts any object that implements the required
            interface, demonstrating interface-based programming.
        """
        self._api = api
        self._entity_id = entity_id

    @property
    def entity_id(self) -> str:
        """
        Get the entity ID for this handler.
        
        This property provides read-only access to the entity_id,
        following encapsulation principles.
        
        Returns:
            str: The Home Assistant entity ID
        """
        return self._entity_id

    @property
    def api(self):
        """
        Expose underlying API (HomeAssistantAPI) to subclasses.
        
        This property provides protected access to the API instance,
        allowing subclasses to interact with Home Assistant while
        maintaining encapsulation of the internal _api attribute.
        
        Returns:
            The Home Assistant API instance (or compatible object)
        """
        return self._api

    def call_service(self, domain: str, service: str, extra: dict | None = None) -> Any:
        """
        Convenience wrapper around api.call_service.
        
        This method demonstrates the Template Method pattern and follows
        the Single Responsibility Principle (SRP) by providing a single,
        consistent way to call Home Assistant services. It encapsulates
        the common pattern of including the entity_id in service calls.
        
        Most device handlers will use this instead of manually
        constructing URLs or headers, promoting code reuse and consistency.
        
        Args:
            domain (str): The Home Assistant domain (e.g., "light", "climate")
            service (str): The service name (e.g., "turn_on", "set_temperature")
            extra (dict | None): Additional parameters for the service call
            
        Returns:
            Any: The result from the API call_service method
            
        Example:
            >>> handler.call_service("light", "turn_on")
            >>> handler.call_service("climate", "set_temperature", {"temperature": 21.0})
        """
        return self._api.call_service(domain, service, self._entity_id, extra=extra)

    @abc.abstractmethod
    def set_state(self, entity_point: str, value: Any) -> None:
        """
        Abstract method to set the device state for a specific attribute.
        
        This abstract method enforces the Template Method pattern and
        follows the Open/Closed Principle (OCP). Each concrete handler
        must implement this method, but the base class defines the
        contract that all handlers must follow.
        
        The method follows the Single Responsibility Principle (SRP) by
        having a single, well-defined purpose: setting device state.
        
        Args:
            entity_point (str): The attribute to set (e.g., "state", "brightness", "temperature")
            value (Any): The value to set for the attribute
            
        Raises:
            NotImplementedError: Must be implemented by concrete subclasses
            ValueError: If entity_point is unsupported or value is invalid
            
        Note:
            Implemented by each concrete handler according to the device type's
            specific requirements. This allows for polymorphism and follows
            the Liskov Substitution Principle (LSP).
        """
        raise NotImplementedError
