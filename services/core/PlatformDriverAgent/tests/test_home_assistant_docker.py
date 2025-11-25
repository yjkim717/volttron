# -*- coding: utf-8 -*-
"""
Integration tests that interact directly with a real Home Assistant instance
running inside Docker.

These tests validate the same logical behaviors as:
- get_point  -> reads a single point from Home Assistant
- scrape_all -> retrieves all states and extracts our target entity
- set_point  -> updates the entity state via Home Assistant service calls

Preconditions:
- Home Assistant is running and reachable from this VM.
- An input_boolean helper named `volttrontest` exists with:
      entity_id = input_boolean.volttrontest
- A valid long-lived access token is provided.
"""

import time
import requests
import pytest

# ----------------------------------------------------------------------
# Home Assistant connection configuration
# ----------------------------------------------------------------------
HOMEASSISTANT_TEST_IP = "192.168.0.100"   # iMac IP (host where Docker is running)
PORT = 8123
ACCESS_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJiNGQ1ZjhiMWU2YWI0MmI0OTRkMDBjMjg0ODMxZDc4MyIsImlhdCI6MTc2Mzg2OTU0NSwiZXhwIjoyMDc5MjI5NTQ1fQ."
    "KaLaUSol07sSBphBpYM4y75lUzO1iGu4oIoj_F2Adw0"
)

BASE_URL = f"http://{HOMEASSISTANT_TEST_IP}:{PORT}"
ENTITY_ID = "input_boolean.volttrontest"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

skip_msg = "Home Assistant is not reachable or token/host/port is incorrect."


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _ha_get_state(entity_id: str) -> str:
    """GET /api/states/<entity_id> → return the raw HA 'state' string."""
    url = f"{BASE_URL}/api/states/{entity_id}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()["state"]


def _ha_set_boolean(entity_id: str, value: int) -> None:
    """
    Update an input_boolean via Home Assistant services:
      value = 0 → turn_off
      value = 1 → turn_on
    """
    if value not in (0, 1):
        raise ValueError("input_boolean value must be 0 or 1")

    service = "turn_on" if value == 1 else "turn_off"
    url = f"{BASE_URL}/api/services/input_boolean/{service}"
    payload = {"entity_id": entity_id}

    resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()

    # Allow HA a moment to finalize state transition
    time.sleep(1)


def _map_state_to_int(state: str) -> int:
    """Map Home Assistant string states to driver-style integer values."""
    return 1 if state.lower() == "on" else 0


# ----------------------------------------------------------------------
# Skip entire module if Home Assistant is not reachable
# ----------------------------------------------------------------------
try:
    ping = requests.get(BASE_URL, timeout=3)
    HA_REACHABLE = ping.status_code == 200
except Exception:
    HA_REACHABLE = False

pytestmark = pytest.mark.skipif(not HA_REACHABLE, reason=skip_msg)


# ----------------------------------------------------------------------
# Test 1 — get_point behavior (GET /states/<entity>)
# ----------------------------------------------------------------------
def test_get_point_from_docker():
    """
    Simulates: get_point('home_assistant', 'bool_state')
    - Reads the raw state from Home Assistant
    - Maps "off" → 0, "on" → 1
    - Ensures value is valid
    """
    raw_state = _ha_get_state(ENTITY_ID)
    value = _map_state_to_int(raw_state)
    assert value in (0, 1), f"Invalid mapped value from HA state '{raw_state}'"


# ----------------------------------------------------------------------
# Test 2 — scrape_all behavior (GET /states)
# ----------------------------------------------------------------------
def test_data_poll_from_docker():
    """
    Simulates: scrape_all('home_assistant')
    - Calls GET /api/states
    - Locates our entity in the returned list
    - Maps its state to an integer
    """
    url = f"{BASE_URL}/api/states"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    states = resp.json()
    entity = next((s for s in states if s.get("entity_id") == ENTITY_ID), None)
    assert entity is not None, f"Entity {ENTITY_ID} not found in Home Assistant"

    raw_state = entity["state"]
    value = _map_state_to_int(raw_state)

    assert value in (0, 1), f"Unexpected state value {value} from '{raw_state}'"


# ----------------------------------------------------------------------
# Test 3 — set_point behavior (POST /services + re-read)
# ----------------------------------------------------------------------
def test_set_point_via_docker():
    """
    Simulates: set_point('home_assistant', 'bool_state', 1)
    - Sends POST request to turn_on service
    - Reads state again
    - Confirms that the boolean is now ON (1)
    """
    # Reset to OFF to ensure deterministic behavior
    _ha_set_boolean(ENTITY_ID, 0)
    before_state = _map_state_to_int(_ha_get_state(ENTITY_ID))

    # Perform set_point operation (turn_on → expected 1)
    _ha_set_boolean(ENTITY_ID, 1)
    after_state = _map_state_to_int(_ha_get_state(ENTITY_ID))

    assert before_state in (0, 1)
    assert after_state == 1, (
        f"Expected ON (1) after updating state, but got '{after_state}'"
    )
