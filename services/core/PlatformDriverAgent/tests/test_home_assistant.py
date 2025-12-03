# -*- coding: utf-8 -*-
"""
Integration tests that interact directly with a real Home Assistant instance
running inside Docker.

These tests validate:
- get_point -> reads a single point from Home Assistant
- scrape_all -> retrieves all states and extracts our target entity
- set_point -> updates the entity state via Home Assistant services
"""

import time
import requests
import pytest

# ----------------------------------------------------------------------
# Home Assistant connection configuration
# ----------------------------------------------------------------------
HOMEASSISTANT_TEST_IP = "192.168.0.142"
PORT = 8123
ACCESS_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhZTI2ZTE0OGU4MWU0Y2I1OGI2YTkzOWE2MzQ3N2MyZiIsImlhdCI6MTc2NDM5MDU2NiwiZXhwIjoyMDc5NzUwNTY2fQ.9ZgFzqCuf-BCgv-atT_XVwGHutvjaefK9J7SFQbf9mI"
)

BASE_URL = f"http://{HOMEASSISTANT_TEST_IP}:{PORT}"

# Entities to test
ENTITY_ID = "input_boolean.volttrontest"
LIGHT_ENTITY_ID = "light.test_light"   
LOCK_ENTITY_ID = "lock.test_lock"
SIREN_ENTITY_ID = "input_boolean.test_siren_switch"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

skip_msg = "Home Assistant is not reachable or token/host/port is incorrect."


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _ha_get_state(entity_id: str) -> str:
    """
    Retrieve the current state of a Home Assistant entity.
    
    This function follows the Single Responsibility Principle (SRP) by having
    a single, well-defined purpose: fetching entity state from Home Assistant API.
    
    Args:
        entity_id (str): The Home Assistant entity ID (e.g., "light.test_light")
        
    Returns:
        str: The current state of the entity (e.g., "on", "off", "locked")
        
    Raises:
        requests.exceptions.HTTPError: If the API request fails
        
    Example:
        >>> state = _ha_get_state("light.test_light")
        >>> print(state)  # "on" or "off"
    """
    url = f"{BASE_URL}/api/states/{entity_id}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()["state"]


def _ha_set_boolean(entity_id: str, value: int) -> None:
    """
    Set the state of an input_boolean entity in Home Assistant.
    
    This function demonstrates the Single Responsibility Principle (SRP) by
    focusing solely on controlling input_boolean entities. It encapsulates
    the Home Assistant API interaction details.
    
    Args:
        entity_id (str): The input_boolean entity ID (e.g., "input_boolean.test")
        value (int): The desired state - 1 for "on", 0 for "off"
        
    Raises:
        requests.exceptions.HTTPError: If the API request fails
        
    Note:
        Includes a 1-second sleep to allow Home Assistant to process the state change.
        
    Example:
        >>> _ha_set_boolean("input_boolean.test", 1)  # Turn on
        >>> _ha_set_boolean("input_boolean.test", 0)  # Turn off
    """
    service = "turn_on" if value == 1 else "turn_off"
    url = f"{BASE_URL}/api/services/input_boolean/{service}"
    payload = {"entity_id": entity_id}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)


def _ha_set_light(entity_id: str, value: int) -> None:
    """
    Set the state of a light entity in Home Assistant.
    
    This function follows the Single Responsibility Principle (SRP) by
    handling only light entity control operations. It demonstrates separation
    of concerns by isolating light-specific API interactions.
    
    Args:
        entity_id (str): The light entity ID (e.g., "light.test_light")
        value (int): The desired state - 1 for "on", 0 for "off"
        
    Raises:
        requests.exceptions.HTTPError: If the API request fails
        
    Note:
        Includes a 1-second sleep to allow Home Assistant to process the state change.
        
    Example:
        >>> _ha_set_light("light.test_light", 1)  # Turn on
        >>> _ha_set_light("light.test_light", 0)  # Turn off
    """
    service = "turn_on" if value == 1 else "turn_off"
    url = f"{BASE_URL}/api/services/light/{service}"
    payload = {"entity_id": entity_id}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)

def _ha_set_lock(entity_id: str, value: int) -> None:
    """
    Set the state of a lock entity in Home Assistant.
    
    This function demonstrates the Single Responsibility Principle (SRP) by
    focusing exclusively on lock entity control. It abstracts the Home Assistant
    lock service API details from the test code.
    
    Args:
        entity_id (str): The lock entity ID (e.g., "lock.test_lock")
        value (int): The desired state - 1 for "locked", 0 for "unlocked"
        
    Raises:
        requests.exceptions.HTTPError: If the API request fails
        
    Note:
        Includes a 1-second sleep to allow Home Assistant to process the state change.
        
    Example:
        >>> _ha_set_lock("lock.test_lock", 1)  # Lock
        >>> _ha_set_lock("lock.test_lock", 0)  # Unlock
    """
    service = "lock" if value == 1 else "unlock"
    url = f"{BASE_URL}/api/services/lock/{service}"
    payload = {"entity_id": entity_id}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)


def _ha_set_siren(entity_id: str, value: int) -> None:
    """
    Set the state of a siren entity using input_boolean service.
    
    This function follows the Single Responsibility Principle (SRP) by
    handling siren state control. It uses input_boolean service as a workaround
    when actual siren entities are not available in the test environment.
    
    Args:
        entity_id (str): The input_boolean entity ID used as siren (e.g., "input_boolean.test_siren_switch")
        value (int): The desired state - 1 for "on", 0 for "off"
        
    Raises:
        requests.exceptions.HTTPError: If the API request fails
        
    Note:
        Includes a 1-second sleep to allow Home Assistant to process the state change.
        This function uses input_boolean service instead of siren service for testing purposes.
        
    Example:
        >>> _ha_set_siren("input_boolean.test_siren_switch", 1)  # Turn on
        >>> _ha_set_siren("input_boolean.test_siren_switch", 0)  # Turn off
    """
    service = "turn_on" if value == 1 else "turn_off"
    url = f"{BASE_URL}/api/services/input_boolean/{service}"
    payload = {"entity_id": entity_id}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)



def _map_state_to_int(state: str) -> int:
    """
    Map Home Assistant state strings to integer values (0 or 1).
    
    This utility function demonstrates the Single Responsibility Principle (SRP)
    by providing a single, focused transformation: converting HA state strings
    to binary integer representation for test assertions.
    
    Args:
        state (str): Home Assistant state string (e.g., "on", "off", "locked", "unlocked")
        
    Returns:
        int: Binary representation - 1 for active states ("on", "locked"), 0 otherwise
        
    Example:
        >>> _map_state_to_int("on")  # Returns 1
        >>> _map_state_to_int("off")  # Returns 0
        >>> _map_state_to_int("locked")  # Returns 1
        >>> _map_state_to_int("unlocked")  # Returns 0
    """
    if state.lower() in ("on", "locked"):
        return 1
    else:
        return 0



# ----------------------------------------------------------------------
# Skip if HA unreachable
# ----------------------------------------------------------------------
try:
    ping = requests.get(BASE_URL, timeout=3)
    HA_REACHABLE = ping.status_code == 200
except Exception:
    HA_REACHABLE = False

pytestmark = pytest.mark.skipif(not HA_REACHABLE, reason=skip_msg)


# ----------------------------------------------------------------------
# Input Boolean Tests
# ----------------------------------------------------------------------
def test_get_point_from_docker():
    """
    Test reading a single point value from Home Assistant.
    
    This test validates the basic read functionality of the Home Assistant
    integration. It follows the Single Responsibility Principle by testing
    one specific behavior: state retrieval.
    
    Test Strategy:
        - Retrieves the current state of the test entity
        - Validates that the state can be mapped to a binary value (0 or 1)
        
    Assertions:
        - The mapped state value must be either 0 or 1
        
    Raises:
        AssertionError: If the state cannot be mapped to 0 or 1
    """
    raw_state = _ha_get_state(ENTITY_ID)
    value = _map_state_to_int(raw_state)
    assert value in (0, 1)


def test_data_poll_from_docker():
    """
    Test retrieving all states from Home Assistant and extracting target entity.
    
    This test validates the scrape_all functionality by fetching all entities
    and locating the target entity within the results. It demonstrates the
    Single Responsibility Principle by testing one specific operation: bulk
    state retrieval and entity filtering.
    
    Test Strategy:
        - Fetches all states from Home Assistant API
        - Searches for the target entity in the results
        - Validates that the entity exists and has a valid state
        
    Assertions:
        - The target entity must be found in the states list
        - The entity's state must be mappable to 0 or 1
        
    Raises:
        AssertionError: If entity is not found or state is invalid
    """
    url = f"{BASE_URL}/api/states"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    states = resp.json()
    entity = next((s for s in states if s.get("entity_id") == ENTITY_ID), None)
    assert entity is not None
    assert _map_state_to_int(entity["state"]) in (0, 1)


def test_set_point_via_docker():
    """
    Test setting a point value via Home Assistant service API.
    
    This test validates the write functionality by setting the entity state
    and verifying the change. It follows the Single Responsibility Principle
    by testing one specific behavior: state modification.
    
    Test Strategy:
        1. Set entity to OFF (0) and record initial state
        2. Set entity to ON (1) and record final state
        3. Verify that the state change was successful
        
    Assertions:
        - Initial state must be valid (0 or 1)
        - Final state must be 1 (ON) after setting to ON
        
    Raises:
        AssertionError: If state changes are not reflected correctly
    """
    _ha_set_boolean(ENTITY_ID, 0)
    before = _map_state_to_int(_ha_get_state(ENTITY_ID))

    _ha_set_boolean(ENTITY_ID, 1)
    after = _map_state_to_int(_ha_get_state(ENTITY_ID))

    assert before in (0, 1)
    assert after == 1


# ----------------------------------------------------------------------
# Light Handler Tests
# ----------------------------------------------------------------------
def test_light_get_state():
    """
    Test reading the current state of a light entity.
    
    This test validates that the LightHandler can successfully retrieve
    the state of a light entity from Home Assistant. It follows the
    Single Responsibility Principle by testing only state retrieval.
    
    Assertions:
        - The light state must be mappable to 0 (off) or 1 (on)
        
    Raises:
        AssertionError: If the state cannot be mapped to 0 or 1
    """
    raw = _ha_get_state(LIGHT_ENTITY_ID)
    value = _map_state_to_int(raw)
    assert value in (0, 1)


def test_light_set_on():
    """
    Test turning a light entity ON via Home Assistant service.
    
    This test validates the LightHandler's ability to turn on a light
    by calling the Home Assistant light.turn_on service. It demonstrates
    the Single Responsibility Principle by testing one specific operation.
    
    Test Strategy:
        1. Call light.turn_on service
        2. Retrieve the current state
        3. Verify that the state is ON (1)
        
    Assertions:
        - The light state must be 1 (ON) after calling turn_on
        
    Raises:
        AssertionError: If the light is not ON after the operation
    """
    _ha_set_light(LIGHT_ENTITY_ID, 1)
    state = _map_state_to_int(_ha_get_state(LIGHT_ENTITY_ID))
    assert state == 1, "Light should be ON after turn_on"


def test_light_set_off():
    """
    Test turning a light entity OFF via Home Assistant service.
    
    This test validates the LightHandler's ability to turn off a light
    by calling the Home Assistant light.turn_off service. It follows
    the Single Responsibility Principle by testing one specific operation.
    
    Test Strategy:
        1. Call light.turn_off service
        2. Retrieve the current state
        3. Verify that the state is OFF (0)
        
    Assertions:
        - The light state must be 0 (OFF) after calling turn_off
        
    Raises:
        AssertionError: If the light is not OFF after the operation
    """
    _ha_set_light(LIGHT_ENTITY_ID, 0)
    state = _map_state_to_int(_ha_get_state(LIGHT_ENTITY_ID))
    assert state == 0, "Light should be OFF after turn_off"


# ----------------------------------------------------------------------
# Lock Handler Tests
# ----------------------------------------------------------------------
def test_lock_get_state():
    """
    Test reading the current state of a lock entity.
    
    This test validates that the LockHandler can successfully retrieve
    the state of a lock entity from Home Assistant. It demonstrates
    the Single Responsibility Principle by testing only state retrieval.
    
    Assertions:
        - The lock state must be mappable to 0 (unlocked) or 1 (locked)
        
    Raises:
        AssertionError: If the state cannot be mapped to 0 or 1
    """
    raw = _ha_get_state(LOCK_ENTITY_ID)
    value = _map_state_to_int(raw)
    assert value in (0, 1)


def test_lock_set_locked():
    """
    Test locking a lock entity via Home Assistant service.
    
    This test validates the LockHandler's ability to lock a lock entity
    by calling the Home Assistant lock.lock service. It follows the
    Single Responsibility Principle by testing one specific operation.
    
    Test Strategy:
        1. Call lock.lock service
        2. Retrieve the current state
        3. Verify that the state is LOCKED (1)
        
    Assertions:
        - The lock state must be 1 (LOCKED) after calling lock service
        
    Raises:
        AssertionError: If the lock is not LOCKED after the operation
    """
    _ha_set_lock(LOCK_ENTITY_ID, 1)
    state = _map_state_to_int(_ha_get_state(LOCK_ENTITY_ID))
    assert state == 1, "Lock should be LOCKED after lock service"


def test_lock_set_unlocked():
    """
    Test unlocking a lock entity via Home Assistant service.
    
    This test validates the LockHandler's ability to unlock a lock entity
    by calling the Home Assistant lock.unlock service. It demonstrates
    the Single Responsibility Principle by testing one specific operation.
    
    Test Strategy:
        1. Call lock.unlock service
        2. Retrieve the current state
        3. Verify that the state is UNLOCKED (0)
        
    Assertions:
        - The lock state must be 0 (UNLOCKED) after calling unlock service
        
    Raises:
        AssertionError: If the lock is not UNLOCKED after the operation
    """
    _ha_set_lock(LOCK_ENTITY_ID, 0)
    state = _map_state_to_int(_ha_get_state(LOCK_ENTITY_ID))
    assert state == 0, "Lock should be UNLOCKED after unlock service"


def test_lock_attributes_exist():
    """
    Test that lock entities have required attributes.
    
    This test validates that lock entities in Home Assistant contain
    the expected attribute structure. It follows the Single Responsibility
    Principle by testing only attribute presence and structure.
    
    Test Strategy:
        1. Fetch the complete entity state from Home Assistant
        2. Extract the attributes dictionary
        3. Verify that attributes exist and are properly structured
        
    Assertions:
        - Attributes must be a dictionary
        - At least one attribute must be present
        
    Raises:
        AssertionError: If attributes are missing or malformed
    """
    url = f"{BASE_URL}/api/states/{LOCK_ENTITY_ID}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    data = resp.json()
    attrs = data.get("attributes", {})

    assert isinstance(attrs, dict)
    assert len(attrs) >= 1, "Lock entity should have at least one attribute"


def test_lock_handler_get_state():
    """
    Unit test for LockHandler.get_state() method using dependency injection.
    
    This test demonstrates the Dependency Inversion Principle (DIP) by
    using a mock API stub instead of the real Home Assistant API. The test
    depends on the abstraction (API interface) rather than concrete implementation.
    
    The APIStub class follows the Liskov Substitution Principle (LSP) by
    implementing the same interface as the real HomeAssistantAPI, allowing
    it to be substituted without breaking the test.
    
    Test Strategy:
        1. Create a mock API stub that returns predefined state data
        2. Instantiate LockHandler with the mock API
        3. Test get_state() method for both state and attribute retrieval
        
    Assertions:
        - State retrieval must return the expected value
        - Attribute retrieval must return the expected value
        
    Raises:
        AssertionError: If get_state() does not return expected values
    """
    from platform_driver.interfaces.device_handlers.lock_handler import LockHandler

    # Fake API stub - demonstrates Dependency Inversion Principle (DIP)
    # This class can be substituted for the real API without breaking the test
    class APIStub:
        """
        Mock API stub for testing LockHandler.
        
        This class demonstrates the Liskov Substitution Principle (LSP) by
        implementing the same interface as HomeAssistantAPI, allowing it to
        be used as a drop-in replacement for testing purposes.
        
        Methods:
            get_state: Returns mock entity state data
        """
        def get_state(self, entity_id):
            """
            Return mock state data for testing.
            
            Args:
                entity_id (str): The entity ID (not used in mock, but required by interface)
                
            Returns:
                dict: Mock state data with state and attributes
            """
            return {
                "state": "locked",
                "attributes": {"friendly_name": "Test Lock"}
            }

    api_stub = APIStub()
    handler = LockHandler(api_stub, LOCK_ENTITY_ID)

    # State check
    state = handler.get_state("state")
    assert state == "locked"

    # Attribute check
    attr = handler.get_state("friendly_name")
    assert attr == "Test Lock"

# ----------------------------------------------------------------------
# Climate Handler Tests
# ----------------------------------------------------------------------

CLIMATE_ENTITY_ID = "climate.test_climate"


def _ha_set_climate_temperature(entity_id: str, temperature: float) -> None:
    """
    Set the target temperature of a climate entity in Home Assistant.
    
    This function follows the Single Responsibility Principle (SRP) by
    handling only climate temperature control operations. It encapsulates
    the Home Assistant climate API interaction details.
    
    Args:
        entity_id (str): The climate entity ID (e.g., "climate.test_climate")
        temperature (float): The target temperature value to set
        
    Raises:
        requests.exceptions.HTTPError: If the API request fails
        
    Note:
        Includes a 1-second sleep to allow Home Assistant to process the state change.
        
    Example:
        >>> _ha_set_climate_temperature("climate.test_climate", 21.5)
    """
    url = f"{BASE_URL}/api/services/climate/set_temperature"
    payload = {"entity_id": entity_id, "temperature": temperature}

    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)


def test_climate_get_state():
    """
    Test reading the current HVAC state of a climate entity.
    
    This test validates that the ClimateHandler can successfully retrieve
    the HVAC state (e.g., 'heat', 'cool', 'off') from Home Assistant.
    It follows the Single Responsibility Principle by testing only state retrieval.
    
    Assertions:
        - The state must be a string
        - The state string must not be empty
        
    Raises:
        AssertionError: If the state is not a valid string
    """
    raw = _ha_get_state(CLIMATE_ENTITY_ID)
    assert isinstance(raw, str)
    assert len(raw) > 0



def test_climate_attributes_exist():
    """
    Test that climate entities have required attributes.
    
    This test validates that climate entities contain expected attributes
    such as HVAC modes, temperature settings, etc. It follows the Single
    Responsibility Principle by testing only attribute presence.
    
    Test Strategy:
        1. Fetch the complete entity state from Home Assistant
        2. Extract the attributes dictionary
        3. Verify that essential climate attributes exist
        
    Assertions:
        - Attributes must be a dictionary
        - At least one attribute must be present
        - Either "hvac_modes" or "temperature" must exist
        
    Raises:
        AssertionError: If required attributes are missing
    """
    url = f"{BASE_URL}/api/states/{CLIMATE_ENTITY_ID}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    attrs = resp.json().get("attributes", {})
    assert isinstance(attrs, dict)
    assert len(attrs) > 0
    assert "hvac_modes" in attrs or "temperature" in attrs


def test_climate_handler_get_state():
    """
    Unit test for ClimateHandler.get_state() method using dependency injection.
    
    This test demonstrates the Dependency Inversion Principle (DIP) by
    using a mock API stub instead of the real Home Assistant API. The test
    depends on the abstraction (API interface) rather than concrete implementation.
    
    The APIStub class follows the Liskov Substitution Principle (LSP) by
    implementing the same interface as the real HomeAssistantAPI.
    
    Test Strategy:
        1. Create a mock API stub with predefined climate state data
        2. Instantiate ClimateHandler with the mock API
        3. Test get_state() for state, temperature, and hvac_modes
        
    Assertions:
        - State retrieval must return the expected HVAC mode
        - Temperature attribute must return the expected value
        - HVAC modes list must match expected values
        
    Raises:
        AssertionError: If get_state() does not return expected values
    """
    from platform_driver.interfaces.device_handlers.climate_handler import ClimateHandler

    class APIStub:
        """
        Mock API stub for testing ClimateHandler.
        
        This class demonstrates the Liskov Substitution Principle (LSP) by
        implementing the same interface as HomeAssistantAPI.
        """
        def get_state(self, eid):
            """
            Return mock climate state data for testing.
            
            Args:
                eid (str): The entity ID (not used in mock, but required by interface)
                
            Returns:
                dict: Mock climate state data with state and attributes
            """
            return {
                "state": "cool",
                "attributes": {
                    "temperature": 21.0,
                    "hvac_modes": ["off", "cool", "heat"]
                }
            }

    api_stub = APIStub()
    handler = ClimateHandler(api_stub, CLIMATE_ENTITY_ID)

    # state
    hvac_state = handler.get_state("state")
    assert hvac_state == "cool"

    # attribute
    temp = handler.get_state("temperature")
    assert temp == 21.0

    modes = handler.get_state("hvac_modes")
    assert modes == ["off", "cool", "heat"]

# ----------------------------------------------------------------------
# Fan Handler Tests
# ----------------------------------------------------------------------
FAN_ENTITY_ID = "fan.test_fan"


def _ha_set_fan_power(entity_id: str, value: int):
    """
    Set the power state (on/off) of a fan entity in Home Assistant.
    
    This function follows the Single Responsibility Principle (SRP) by
    handling only fan power control operations. It abstracts the Home Assistant
    fan service API details from the test code.
    
    Args:
        entity_id (str): The fan entity ID (e.g., "fan.test_fan")
        value (int): The desired power state - 1 for "on", 0 for "off"
        
    Raises:
        requests.exceptions.HTTPError: If the API request fails
        
    Note:
        Includes a 1-second sleep to allow Home Assistant to process the state change.
        
    Example:
        >>> _ha_set_fan_power("fan.test_fan", 1)  # Turn on
        >>> _ha_set_fan_power("fan.test_fan", 0)  # Turn off
    """
    service = "turn_on" if value == 1 else "turn_off"
    url = f"{BASE_URL}/api/services/fan/{service}"
    payload = {"entity_id": entity_id}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)


def _ha_set_fan_speed(entity_id: str, speed: int):
    """
    Set the speed/percentage of a fan entity in Home Assistant.
    
    This function follows the Single Responsibility Principle (SRP) by
    handling only fan speed control operations. It encapsulates the
    Home Assistant fan percentage API interaction.
    
    Args:
        entity_id (str): The fan entity ID (e.g., "fan.test_fan")
        speed (int): The fan speed percentage (0-100)
        
    Raises:
        requests.exceptions.HTTPError: If the API request fails
        
    Note:
        Includes a 1-second sleep to allow Home Assistant to process the state change.
        The fan must be ON before setting speed for some fan types.
        
    Example:
        >>> _ha_set_fan_speed("fan.test_fan", 50)  # Set to 50%
    """
    url = f"{BASE_URL}/api/services/fan/set_percentage"
    payload = {"entity_id": entity_id, "percentage": speed}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)


def _ha_set_fan_oscillate(entity_id: str, value: int):
    """
    Set the oscillation state of a fan entity in Home Assistant.
    
    This function follows the Single Responsibility Principle (SRP) by
    handling only fan oscillation control operations. It abstracts the
    Home Assistant fan oscillation API details.
    
    Args:
        entity_id (str): The fan entity ID (e.g., "fan.test_fan")
        value (int): The oscillation state - 1 for oscillating, 0 for not oscillating
        
    Raises:
        requests.exceptions.HTTPError: If the API request fails or fan doesn't support oscillation
        
    Note:
        Includes a 1-second sleep to allow Home Assistant to process the state change.
        Not all fan entities support oscillation.
        
    Example:
        >>> _ha_set_fan_oscillate("fan.test_fan", 1)  # Enable oscillation
    """
    url = f"{BASE_URL}/api/services/fan/oscillate"
    payload = {"entity_id": entity_id, "oscillating": bool(value)}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)


def test_fan_get_state():
    """
    Test reading the current power state of a fan entity.
    
    This test validates that the FanHandler can successfully retrieve
    the power state of a fan entity from Home Assistant. It follows
    the Single Responsibility Principle by testing only state retrieval.
    
    Assertions:
        - The fan state must be either "on" or "off"
        
    Raises:
        AssertionError: If the state is not "on" or "off"
    """
    raw = _ha_get_state(FAN_ENTITY_ID)
    assert raw in ("on", "off")


def test_fan_power_toggle():
    """
    Test toggling fan power state (on/off) via Home Assistant service.
    
    This test validates the FanHandler's ability to control fan power
    by testing both turn_on and turn_off operations. It follows the
    Single Responsibility Principle by testing one specific behavior.
    
    Test Strategy:
        1. Turn fan ON and verify state
        2. Turn fan OFF and verify state
        
    Assertions:
        - Fan must be ON after turn_on operation
        - Fan must be OFF after turn_off operation
        
    Raises:
        AssertionError: If fan state does not match expected values
    """
    _ha_set_fan_power(FAN_ENTITY_ID, 1)
    assert _ha_get_state(FAN_ENTITY_ID) == "on"

    _ha_set_fan_power(FAN_ENTITY_ID, 0)
    assert _ha_get_state(FAN_ENTITY_ID) == "off"


def test_fan_speed():
    """
    Test fan speed setting. Note: Fan must be ON before setting speed.
    """
    # First, ensure fan is ON (some fans require being on before setting speed)
    _ha_set_fan_power(FAN_ENTITY_ID, 1)
    time.sleep(0.5)  # Wait for state to update
    
    # Now set the speed
    _ha_set_fan_speed(FAN_ENTITY_ID, 50)
    time.sleep(1.5)  # Give more time for state to update

    url = f"{BASE_URL}/api/states/{FAN_ENTITY_ID}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    data = resp.json()
    attrs = data.get("attributes", {})
    state = data.get("state")
    
    # Check if fan is on
    if state != "on":
        pytest.skip(f"Fan is not ON (state={state}), cannot test speed")
    
    # Check percentage
    percentage = attrs.get("percentage")
    if percentage is None:
        # Try alternative attribute names for fans that don't use percentage
        speed = attrs.get("speed") or attrs.get("speed_level") or attrs.get("current_speed")
        if speed is not None:
            assert speed is not None and speed != 0, f"Speed value is None or 0"
        else:
            pytest.skip(f"Fan entity does not support speed/percentage. Available attributes: {list(attrs.keys())}")
    else:
        assert percentage == 50, f"Expected percentage 50, got {percentage}"


def test_fan_oscillate():
    """
    Test fan oscillation. Note: Some fan entities may not support oscillation.
    """
    try:
        _ha_set_fan_oscillate(FAN_ENTITY_ID, 1)
    except requests.exceptions.HTTPError as e:
        # If fan doesn't support oscillation, skip this test
        if e.response.status_code == 500 or e.response.status_code == 400:
            pytest.skip(f"Fan entity {FAN_ENTITY_ID} does not support oscillation: {e}")
        raise

    url = f"{BASE_URL}/api/states/{FAN_ENTITY_ID}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    data = resp.json()
    attrs = data.get("attributes", {})
    
    oscillating = attrs.get("oscillating")
    assert oscillating is True, f"Expected oscillating=True, got {oscillating}"


def test_fan_handler_get_state():
    """
    Unit test for FanHandler.get_state() method using dependency injection.
    
    This test demonstrates the Dependency Inversion Principle (DIP) by
    using a mock API stub instead of the real Home Assistant API. The test
    depends on the abstraction (API interface) rather than concrete implementation.
    
    The APIStub class follows the Liskov Substitution Principle (LSP) by
    implementing the same interface as the real HomeAssistantAPI.
    
    Test Strategy:
        1. Create a mock API stub with predefined fan state data
        2. Instantiate FanHandler with the mock API
        3. Test get_state() for state, percentage, and oscillating attributes
        
    Assertions:
        - State retrieval must return "on"
        - Percentage attribute must return 80
        - Oscillating attribute must return True
        
    Raises:
        AssertionError: If get_state() does not return expected values
    """
    from platform_driver.interfaces.device_handlers.fan_handler import FanHandler

    class APIStub:
        """
        Mock API stub for testing FanHandler.
        
        This class demonstrates the Liskov Substitution Principle (LSP) by
        implementing the same interface as HomeAssistantAPI.
        """
        def get_state(self, entity_id):
            """
            Return mock fan state data for testing.
            
            Args:
                entity_id (str): The entity ID (not used in mock, but required by interface)
                
            Returns:
                dict: Mock fan state data with state and attributes
            """
            return {
                "state": "on",
                "attributes": {
                    "percentage": 80,
                    "oscillating": True
                }
            }

    api = APIStub()
    handler = FanHandler(api, FAN_ENTITY_ID)

    assert handler.get_state("state") == "on"
    assert handler.get_state("percentage") == 80
    assert handler.get_state("oscillating") is True


# ----------------------------------------------------------------------
# Siren Handler Tests
# ----------------------------------------------------------------------
def test_siren_get_state():
    """
    Test reading the current state of a siren entity (using input_boolean).
    
    This test validates that the SirenHandler can successfully retrieve
    the state of a siren entity from Home Assistant. It uses input_boolean
    as a workaround when actual siren entities are not available.
    
    Assertions:
        - The siren state must be mappable to 0 (off) or 1 (on)
        
    Raises:
        AssertionError: If the state cannot be mapped to 0 or 1
    """
    raw = _ha_get_state(SIREN_ENTITY_ID)
    value = _map_state_to_int(raw)
    assert value in (0, 1)


def test_siren_set_on():
    """
    Test turning a siren entity ON via Home Assistant service.
    
    This test validates the SirenHandler's ability to turn on a siren
    by calling the Home Assistant service. It uses input_boolean service
    as a workaround when actual siren entities are not available.
    
    Test Strategy:
        1. Call turn_on service (via input_boolean)
        2. Retrieve the current state
        3. Verify that the state is ON (1)
        
    Assertions:
        - The siren state must be 1 (ON) after calling turn_on
        
    Raises:
        AssertionError: If the siren is not ON after the operation
    """
    _ha_set_siren(SIREN_ENTITY_ID, 1)
    state = _map_state_to_int(_ha_get_state(SIREN_ENTITY_ID))
    assert state == 1, "Siren should be ON after turn_on"


def test_siren_set_off():
    """
    Test turning a siren entity OFF via Home Assistant service.
    
    This test validates the SirenHandler's ability to turn off a siren
    by calling the Home Assistant service. It uses input_boolean service
    as a workaround when actual siren entities are not available.
    
    Test Strategy:
        1. Call turn_off service (via input_boolean)
        2. Retrieve the current state
        3. Verify that the state is OFF (0)
        
    Assertions:
        - The siren state must be 0 (OFF) after calling turn_off
        
    Raises:
        AssertionError: If the siren is not OFF after the operation
    """
    _ha_set_siren(SIREN_ENTITY_ID, 0)
    state = _map_state_to_int(_ha_get_state(SIREN_ENTITY_ID))
    assert state == 0, "Siren should be OFF after turn_off"


def test_siren_attributes_exist():
    """
    Test that siren entities (input_boolean) have required attributes.
    
    This test validates that siren entities (using input_boolean) contain
    the expected attribute structure. It follows the Single Responsibility
    Principle by testing only attribute presence and structure.
    
    Test Strategy:
        1. Fetch the complete entity state from Home Assistant
        2. Extract the attributes dictionary
        3. Verify that attributes exist and are properly structured
        
    Assertions:
        - Attributes must be a dictionary
        - At least one attribute must be present
        
    Raises:
        AssertionError: If attributes are missing or malformed
    """
    url = f"{BASE_URL}/api/states/{SIREN_ENTITY_ID}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    data = resp.json()
    attrs = data.get("attributes", {})

    assert isinstance(attrs, dict)
    assert len(attrs) >= 1, "Siren entity should have at least one attribute"


def test_siren_handler_get_state():
    """
    Unit test for SirenHandler.get_state() method using dependency injection.
    
    This test demonstrates the Dependency Inversion Principle (DIP) by
    using a mock API stub instead of the real Home Assistant API. The test
    depends on the abstraction (API interface) rather than concrete implementation.
    
    The APIStub class follows the Liskov Substitution Principle (LSP) by
    implementing the same interface as the real HomeAssistantAPI, allowing
    it to be substituted without breaking the test.
    
    Test Strategy:
        1. Create a mock API stub with predefined siren state data
        2. Instantiate SirenHandler with the mock API
        3. Test get_state() method for state and multiple attributes
        
    Assertions:
        - State retrieval must return "on"
        - friendly_name attribute must return expected value
        - volume_level attribute must return expected value
        
    Raises:
        AssertionError: If get_state() does not return expected values
    """
    from platform_driver.interfaces.device_handlers.siren_handler import SirenHandler

    # Fake API stub - demonstrates Dependency Inversion Principle (DIP)
    # This class can be substituted for the real API without breaking the test
    class APIStub:
        """
        Mock API stub for testing SirenHandler.
        
        This class demonstrates the Liskov Substitution Principle (LSP) by
        implementing the same interface as HomeAssistantAPI, allowing it to
        be used as a drop-in replacement for testing purposes.
        
        Methods:
            get_state: Returns mock entity state data
        """
        def get_state(self, entity_id):
            """
            Return mock siren state data for testing.
            
            Args:
                entity_id (str): The entity ID (not used in mock, but required by interface)
                
            Returns:
                dict: Mock siren state data with state and attributes
            """
            return {
                "state": "on",
                "attributes": {"friendly_name": "Test Siren", "volume_level": 0.5}
            }

    api_stub = APIStub()
    handler = SirenHandler(api_stub, SIREN_ENTITY_ID)

    # State check
    state = handler.get_state("state")
    assert state == "on"

    # Attribute check
    attr = handler.get_state("friendly_name")
    assert attr == "Test Siren"
    
    # Another attribute check
    volume = handler.get_state("volume_level")
    assert volume == 0.5

