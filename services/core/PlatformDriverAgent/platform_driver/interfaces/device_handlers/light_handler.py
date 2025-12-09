# -*- coding: utf-8 -*-
"""
LightHandler

Handler for Home Assistant light entities.
This handler demonstrates the Single Responsibility Principle (SRP) by
focusing exclusively on light device control operations (on/off).

The class follows the Open/Closed Principle (OCP) by extending BaseDeviceHandler
without modifying it, and the Liskov Substitution Principle (LSP) by properly
implementing the abstract set_state() method.
"""

import logging
from .base_handler import BaseDeviceHandler

_log = logging.getLogger(__name__)


class LightHandler(BaseDeviceHandler):
    """
    Light Handler for Home Assistant light entities.
    
    This handler demonstrates the Single Responsibility Principle (SRP) by
    having a single, well-defined purpose: controlling light devices (on/off).
    It provides a simple interface for turning lights on or off via Home
    Assistant's light service API.
    
    The class follows the Open/Closed Principle (OCP) by extending
    BaseDeviceHandler without modifying the base class. It also follows
    the Liskov Substitution Principle (LSP) by properly implementing
    all abstract methods from the base class.
    
    Supported operations:
    - Turn light ON via set_state("state", 1)
    - Turn light OFF via set_state("state", 0)
    """

    def set_state(self, entity_point, value):
        """
        Set the state of a light entity (on or off).
        
        This method demonstrates the Single Responsibility Principle (SRP)
        by handling only light power state control. It validates the input
        value and delegates to the appropriate Home Assistant service.
        
        The method uses the Template Method pattern by calling the parent
        class's call_service() method, promoting code reuse and consistency.
        
        Args:
            entity_point (str): The attribute to set. Typically "state"
            value (int): The desired state:
                - 1: Turn the light ON (calls light.turn_on)
                - 0: Turn the light OFF (calls light.turn_off)
        
        Raises:
            ValueError: If value is not 0 or 1
            
        Example:
            >>> handler.set_state("state", 1)  # Turn on
            >>> handler.set_state("state", 0)  # Turn off
        """
        if value not in (0, 1):
            raise ValueError("Light state must be 0 (off) or 1 (on).")

        service = "turn_on" if value == 1 else "turn_off"

        _log.info(
            "[LIGHT] %s → service=%s value=%s",
            self.entity_id, service, value
        )

        # Use parent class's call_service method
        # This demonstrates the Template Method pattern and code reuse
        self.call_service("light", service)
