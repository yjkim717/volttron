# -*- coding: utf-8 -*-
"""
InputBooleanHandler

Handler for Home Assistant input_boolean entities.
This handler is primarily used for testing purposes in pytest.

This handler demonstrates the Single Responsibility Principle (SRP) by
focusing exclusively on input_boolean device control operations.
"""

from .base_handler import BaseDeviceHandler


class InputBooleanHandler(BaseDeviceHandler):
    """
    Simple handler for input_boolean entities used in pytest tests.
    
    This handler demonstrates the Single Responsibility Principle (SRP) by
    having a single, well-defined purpose: controlling input_boolean entities
    (which are test/helper entities in Home Assistant).
    
    The class follows the Open/Closed Principle (OCP) by extending
    BaseDeviceHandler without modifying the base class. It also follows
    the Liskov Substitution Principle (LSP) by properly implementing
    the abstract set_state() method.
    
    Note:
        This handler is primarily used for integration testing and may not
        be used in production code. Input booleans are typically helper
        entities in Home Assistant for automation and testing.
    
    Supported operations:
    - Turn input_boolean ON via set_state(entity_point, 1)
    - Turn input_boolean OFF via set_state(entity_point, 0)
    """

    def set_state(self, entity_point, value):
        """
        Set the state of an input_boolean entity (on or off).
        
        This method demonstrates the Single Responsibility Principle (SRP)
        by handling only input_boolean state control. It provides a simple
        binary on/off interface for test entities.
        
        Args:
            entity_point (str): The attribute to set (typically "state").
                               This parameter is accepted for interface
                               compatibility but is not used for input_boolean.
            value (int): The desired state:
                - 1: Turn the input_boolean ON (calls input_boolean.turn_on)
                - 0: Turn the input_boolean OFF (calls input_boolean.turn_off)
        
        Note:
            Input booleans only support binary states (on/off), so any
            non-zero value will turn it on, and zero will turn it off.
            
        Example:
            >>> handler.set_state("state", 1)  # Turn on
            >>> handler.set_state("state", 0)  # Turn off
        """
        if value == 1:
            self.api.call_service("input_boolean", "turn_on", self.entity_id)
        else:
            self.api.call_service("input_boolean", "turn_off", self.entity_id)
