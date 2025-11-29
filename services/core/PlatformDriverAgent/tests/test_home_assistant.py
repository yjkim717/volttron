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


def _map_state_to_int(state: str) -> int:
    return 1 if state.lower() == "on" else 0


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
