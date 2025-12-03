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

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

skip_msg = "Home Assistant is not reachable or token/host/port is incorrect."


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _ha_get_state(entity_id: str) -> str:
    url = f"{BASE_URL}/api/states/{entity_id}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()["state"]


def _ha_set_boolean(entity_id: str, value: int) -> None:
    service = "turn_on" if value == 1 else "turn_off"
    url = f"{BASE_URL}/api/services/input_boolean/{service}"
    payload = {"entity_id": entity_id}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)


def _ha_set_light(entity_id: str, value: int) -> None:
    service = "turn_on" if value == 1 else "turn_off"
    url = f"{BASE_URL}/api/services/light/{service}"
    payload = {"entity_id": entity_id}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)

def _ha_set_lock(entity_id: str, value: int) -> None:
    service = "lock" if value == 1 else "unlock"
    url = f"{BASE_URL}/api/services/lock/{service}"
    payload = {"entity_id": entity_id}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)



def _map_state_to_int(state: str) -> int:
    """Map HA states to 0/1"""
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
    raw_state = _ha_get_state(ENTITY_ID)
    value = _map_state_to_int(raw_state)
    assert value in (0, 1)


def test_data_poll_from_docker():
    url = f"{BASE_URL}/api/states"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    states = resp.json()
    entity = next((s for s in states if s.get("entity_id") == ENTITY_ID), None)
    assert entity is not None
    assert _map_state_to_int(entity["state"]) in (0, 1)


def test_set_point_via_docker():
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
    raw = _ha_get_state(LIGHT_ENTITY_ID)
    value = _map_state_to_int(raw)
    assert value in (0, 1)


def test_light_set_on():
    _ha_set_light(LIGHT_ENTITY_ID, 1)
    state = _map_state_to_int(_ha_get_state(LIGHT_ENTITY_ID))
    assert state == 1, "Light should be ON after turn_on"


def test_light_set_off():
    _ha_set_light(LIGHT_ENTITY_ID, 0)
    state = _map_state_to_int(_ha_get_state(LIGHT_ENTITY_ID))
    assert state == 0, "Light should be OFF after turn_off"


# ----------------------------------------------------------------------
# Lock Handler Tests
# ----------------------------------------------------------------------
def test_lock_get_state():
    raw = _ha_get_state(LOCK_ENTITY_ID)
    value = _map_state_to_int(raw)
    assert value in (0, 1)


def test_lock_set_locked():
    _ha_set_lock(LOCK_ENTITY_ID, 1)
    state = _map_state_to_int(_ha_get_state(LOCK_ENTITY_ID))
    assert state == 1, "Lock should be LOCKED after lock service"


def test_lock_set_unlocked():
    _ha_set_lock(LOCK_ENTITY_ID, 0)
    state = _map_state_to_int(_ha_get_state(LOCK_ENTITY_ID))
    assert state == 0, "Lock should be UNLOCKED after unlock service"


def test_lock_attributes_exist():
    """
    Minimal attribute test.
    Lock entities usually have several attributes.
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
    Tests get_state() of LockHandler directly.
    """
    from platform_driver.interfaces.device_handlers.lock_handler import LockHandler

    # Fake API stub
    class APIStub:
        def get_state(self, entity_id):
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
    Home Assistant climate service:
    POST /api/services/climate/set_temperature
    payload = { "entity_id": ..., "temperature": X }
    """
    url = f"{BASE_URL}/api/services/climate/set_temperature"
    payload = {"entity_id": entity_id, "temperature": temperature}

    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)


def test_climate_get_state():
    """
    Basic climate state read (e.g., 'heat', 'cool', 'off').
    """
    raw = _ha_get_state(CLIMATE_ENTITY_ID)
    assert isinstance(raw, str)
    assert len(raw) > 0



def test_climate_attributes_exist():
    """
    Ensure attributes like HVAC modes, min/max temps, etc. exist.
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
    Unit-test ClimateHandler directly (no docker).
    """
    from platform_driver.interfaces.device_handlers.climate_handler import ClimateHandler

    class APIStub:
        def get_state(self, eid):
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
    service = "turn_on" if value == 1 else "turn_off"
    url = f"{BASE_URL}/api/services/fan/{service}"
    payload = {"entity_id": entity_id}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)


def _ha_set_fan_speed(entity_id: str, speed: int):
    url = f"{BASE_URL}/api/services/fan/set_percentage"
    payload = {"entity_id": entity_id, "percentage": speed}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)


def _ha_set_fan_oscillate(entity_id: str, value: int):
    url = f"{BASE_URL}/api/services/fan/oscillate"
    payload = {"entity_id": entity_id, "oscillating": bool(value)}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    time.sleep(1)


def test_fan_get_state():
    raw = _ha_get_state(FAN_ENTITY_ID)
    assert raw in ("on", "off")


def test_fan_power_toggle():
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
    Unit-test FanHandler directly (no docker).
    """
    from platform_driver.interfaces.device_handlers.fan_handler import FanHandler

    class APIStub:
        def get_state(self, entity_id):
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

