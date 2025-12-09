# services/core/PlatformDriverAgent/platform_driver/interfaces/device_handlers/climate_handler.py
# -*- coding: utf-8 -*-
"""
ClimateHandler

Handler for Home Assistant climate entities (thermostats, HVAC systems).
This handler demonstrates the Single Responsibility Principle (SRP) by
focusing exclusively on climate device control operations.

The class follows the Open/Closed Principle (OCP) by extending BaseDeviceHandler
without modifying it, and the Liskov Substitution Principle (LSP) by properly
implementing the abstract set_state() method.
"""

import logging
from .base_handler import BaseDeviceHandler

_log = logging.getLogger(__name__)


class ClimateHandler(BaseDeviceHandler):
    """
    Climate Handler for Home Assistant climate entities.
    
    This handler demonstrates the Single Responsibility Principle (SRP) by
    having a single, well-defined purpose: managing climate device states.
    It handles HVAC mode control and temperature settings for thermostats
    and HVAC systems in Home Assistant.
    
    The class follows the Open/Closed Principle (OCP) by extending
    BaseDeviceHandler without modifying the base class. It also follows
    the Liskov Substitution Principle (LSP) by properly implementing
    all abstract methods from the base class.
    
    Supported operations:
    - Set HVAC mode (heat/cool/off) via hvac_mode or state entity_point
    - Set target temperature via temperature entity_point
    - Retrieve current state and attributes via get_state()
    
    Attributes:
        SUPPORTED_POINTS (set): Set of supported entity_point names
    """

    SUPPORTED_POINTS = {"temperature", "hvac_mode", "state"}

    def set_state(self, entity_point, value):
        """
        Set the state of a climate entity attribute.
        
        This method demonstrates the Single Responsibility Principle (SRP)
        by handling only climate-specific state setting operations. It
        validates inputs and delegates to the appropriate Home Assistant
        service based on the entity_point type.
        
        The method uses a Strategy-like pattern internally, selecting the
        appropriate service call based on the entity_point parameter.
        
        Args:
            entity_point (str): The attribute to set. Supported values:
                - "temperature" (numeric): Set target temperature
                - "hvac_mode" (string): Set HVAC mode ("heat", "cool", "off")
                - "state" (string): Alias for "hvac_mode"
            value: The value to set:
                - For "temperature": numeric value (float or int)
                - For "hvac_mode" or "state": string ("heat", "cool", "off")
        
        Raises:
            ValueError: If entity_point is not in SUPPORTED_POINTS or is invalid
            
        Example:
            >>> handler.set_state("temperature", 21.5)
            >>> handler.set_state("hvac_mode", "cool")
            >>> handler.set_state("state", "heat")  # Alias for hvac_mode
        """
        if entity_point not in self.SUPPORTED_POINTS:
            raise ValueError(f"Unsupported climate attribute: {entity_point}")

        if entity_point == "temperature":
            service = "set_temperature"
            data = {"entity_id": self.entity_id, "temperature": value}

        elif entity_point in ("hvac_mode", "state"):
            service = "set_hvac_mode"
            data = {"entity_id": self.entity_id, "hvac_mode": value}

        else:
            raise ValueError(f"Invalid entity_point: {entity_point}")

        _log.info(f"[CLIMATE] {self.entity_id} → {entity_point} = {value}")

        self.api.call_service("climate", service, data)

    def get_state(self, entity_point):
        """
        Retrieve the current state or attribute value of a climate entity.
        
        This method demonstrates the Single Responsibility Principle (SRP)
        by handling only state retrieval operations. It provides a unified
        interface for accessing both the main state and entity attributes.
        
        Args:
            entity_point (str): The attribute to retrieve:
                - "state": Returns the current HVAC mode ("heat", "cool", "off")
                - "temperature": Returns the target temperature from attributes
                - Any other string: Returns the corresponding attribute value
        
        Returns:
            Any: The requested state or attribute value, or None if not found
            
        Example:
            >>> handler.get_state("state")  # Returns "heat", "cool", or "off"
            >>> handler.get_state("temperature")  # Returns numeric temperature
            >>> handler.get_state("hvac_modes")  # Returns list of available modes
        """
        state_data = self.api.get_state(self.entity_id)

        if not state_data:
            return None

        if entity_point == "state":
            return state_data.get("state")

        return state_data.get("attributes", {}).get(entity_point)
