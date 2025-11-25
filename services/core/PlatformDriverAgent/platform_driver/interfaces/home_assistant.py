# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2023 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
#
# ===----------------------------------------------------------------------===
# }}}

import logging
import requests

from platform_driver.interfaces import BaseInterface, BaseRegister, BasicRevert
from volttron.platform.agent import utils

# === Existing handlers ===
from device_handlers.light_handler import LightHandler
from device_handlers.switch_handler import SwitchHandler
from device_handlers.climate_handler import ClimateHandler

# === Optional handlers ===
try:
    from device_handlers.lock_handler import LockHandler
except ImportError:
    LockHandler = None

try:
    from device_handlers.fan_handler import FanHandler
except ImportError:
    FanHandler = None

try:
    from device_handlers.siren_handler import SirenHandler
except ImportError:
    SirenHandler = None

_log = logging.getLogger(__name__)

type_mapping = {
    "string": str,
    "int": int,
    "integer": int,
    "float": float,
    "bool": bool,
    "boolean": bool
}

# =====================================================
# Home Assistant REST API
# =====================================================
class HomeAssistantAPI(object):
    """
    Thin wrapper around Home Assistant's REST API.
    Responsible only for HTTP details (URL, headers, logging).
    """

    def __init__(self, ip_address, port, access_token):
        self._base_url = f"http://{ip_address}:{port}/api"
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def get_state(self, entity_id):
        url = f"{self._base_url}/states/{entity_id}"
        resp = requests.get(url, headers=self._headers)
        if resp.status_code == 200:
            return resp.json()

        _log.error("Failed to fetch state for %s: %s", entity_id, resp.text)
        raise Exception(f"Error fetching state for {entity_id}")

    def call_service(self, domain, service, entity_id, extra=None):
        url = f"{self._base_url}/services/{domain}/{service}"
        payload = {"entity_id": entity_id}
        if extra:
            payload.update(extra)

        resp = requests.post(url, headers=self._headers, json=payload)
        if resp.status_code not in (200, 201):
            _log.error("Service call error %s.%s for %s: %s",
                       domain, service, entity_id, resp.text)
            raise Exception(
                f"Error calling {domain}.{service} for {entity_id}: "
                f"{resp.status_code} {resp.text}"
            )
        return resp.json()


# =====================================================
# Input Boolean Handler (pytest 전용)
# =====================================================
class InputBooleanHandler:
    """
    Simple handler used by tests for input_boolean entities.
    Maps 0/1 <-> off/on via Home Assistant services.
    """

    def __init__(self, api: HomeAssistantAPI, entity_id: str):
        self.api = api
        self.entity_id = entity_id

    def set_state(self, entity_point, value):
        # For input_boolean we only care about on/off semantics.
        if value == 1:
            self.api.call_service("input_boolean", "turn_on", self.entity_id)
        else:
            self.api.call_service("input_boolean", "turn_off", self.entity_id)


# =====================================================
# Strategy + Factory: Handler selection
# =====================================================
class HandlerStrategyFactory:
    """
    Strategy/Factory responsible for choosing the correct handler
    implementation for a given Home Assistant entity_id.

    - Keeps mapping from entity_id prefix -> handler class
    - Hides if/elif chain from the Interface
    - Makes it easy to register new handlers (OCP-friendly)
    """

    def __init__(self, api: HomeAssistantAPI):
        self._api = api

        # registry: list of (prefix, handler_cls, name, required_flag)
        self._registry = []

        # === Required handlers ===
        self._register("light.", LightHandler, "LightHandler", required=True)
        self._register("switch.", SwitchHandler, "SwitchHandler", required=True)
        self._register("climate.", ClimateHandler, "ClimateHandler", required=True)
        self._register("input_boolean.", InputBooleanHandler,
                       "InputBooleanHandler", required=True)

        # === Optional handlers (Lock, Fan, Siren) ===
        self._register("lock.", LockHandler, "LockHandler", required=False)
        self._register("fan.", FanHandler, "FanHandler", required=False)
        self._register("siren.", SirenHandler, "SirenHandler", required=False)

    def _register(self, prefix: str, handler_cls, name: str, required: bool):
        """
        Register a handler strategy for a given entity_id prefix.

        :param prefix: e.g. "light.", "climate.", ...
        :param handler_cls: handler class or None (for optional handlers not installed)
        :param name: human-readable name (for error messages)
        :param required: whether this handler must exist
        """
        self._registry.append({
            "prefix": prefix,
            "handler_cls": handler_cls,
            "name": name,
            "required": required
        })

    def get_handler(self, entity_id: str):
        """
        Factory method:
        - Find the first matching prefix for the entity_id.
        - Instantiate the corresponding handler with the shared API.
        """
        for entry in self._registry:
            prefix = entry["prefix"]
            handler_cls = entry["handler_cls"]
            name = entry["name"]
            required = entry["required"]

            if not entity_id.startswith(prefix):
                continue

            # Handler is required but not available → configuration error.
            if handler_cls is None:
                if required:
                    raise ValueError(f"{name} not implemented but required "
                                     f"for entity_id '{entity_id}'.")
                else:
                    raise ValueError(f"Optional handler {name} is not available "
                                     f"for entity_id '{entity_id}'.")

            return handler_cls(self._api, entity_id)

        # No matching prefix at all → unsupported entity type.
        raise ValueError(f"Unsupported entity type for entity_id: {entity_id}")


# =====================================================
# Register Object
# =====================================================
class HomeAssistantRegister(BaseRegister):
    def __init__(
        self, read_only, pointName, units, reg_type,
        attributes, entity_id, entity_point,
        default_value=None, description=''
    ):
        super(HomeAssistantRegister, self).__init__(
            "byte", read_only, pointName, units, description
        )
        self.reg_type = reg_type
        self.attributes = attributes
        self.entity_id = entity_id
        self.entity_point = entity_point
        self.value = default_value


# =====================================================
# Main Interface
# =====================================================
class Interface(BasicRevert, BaseInterface):
    """
    VOLTTRON PlatformDriver interface for Home Assistant.

    Responsibilities:
    - Hold connection config and HomeAssistantAPI instance
    - Parse registry and construct HomeAssistantRegister objects
    - Delegate read/write operations to handler strategies
    """

    def __init__(self, **kwargs):
        super(Interface, self).__init__(**kwargs)
        self.ip_address = None
        self.access_token = None
        self.port = None
        self._api: HomeAssistantAPI | None = None
        self._handler_factory: HandlerStrategyFactory | None = None

    # ----------------------------------------
    def configure(self, config_dict, registry_config_str):
        self.ip_address = config_dict.get("ip_address")
        self.access_token = config_dict.get("access_token")
        self.port = config_dict.get("port")

        if not all([self.ip_address, self.access_token, self.port]):
            raise ValueError("ip_address, access_token, port must be set")

        # Shared API instance used by all handlers
        self._api = HomeAssistantAPI(
            self.ip_address, self.port, self.access_token
        )

        # Strategy/Factory for entity_id -> handler resolution
        self._handler_factory = HandlerStrategyFactory(self._api)

        self.parse_config(registry_config_str)

    # ----------------------------------------
    def get_point(self, point_name):
        reg = self.get_register_by_name(point_name)
        entity_data = self.get_entity_data(reg.entity_id)

        if reg.entity_point == "state":
            raw = entity_data.get("state")
        else:
            raw = entity_data.get("attributes", {}).get(reg.entity_point)

        # Input Boolean → integer
        if reg.entity_id.startswith("input_boolean."):
            return 1 if str(raw).lower() == "on" else 0

        return raw

    # ----------------------------------------
    def _set_point(self, point_name, value):
        reg = self.get_register_by_name(point_name)

        if reg.read_only:
            raise IOError(f"Trying to write to a read-only point {point_name}")

        reg.value = reg.reg_type(value)
        handler = self._get_handler(reg.entity_id)
        handler.set_state(reg.entity_point, reg.value)

        _log.info("[SET] %s → %s = %r",
                  reg.entity_id, reg.entity_point, reg.value)
        return reg.value

    # ----------------------------------------
    def _get_handler(self, entity_id: str):
        """
        Delegates handler selection to HandlerStrategyFactory.
        This replaces the earlier if/elif chain with a Strategy/Factory pattern.
        """
        if self._handler_factory is None:
            raise RuntimeError("HandlerStrategyFactory is not initialized. "
                               "Did you call configure()?")

        return self._handler_factory.get_handler(entity_id)

    # ----------------------------------------
    def _scrape_all(self):
        result = {}
        all_regs = (
            self.get_registers_by_type("byte", True) +
            self.get_registers_by_type("byte", False)
        )

        for reg in all_regs:
            try:
                entity_data = self.get_entity_data(reg.entity_id)

                if reg.entity_id.startswith("input_boolean."):
                    state = entity_data.get("state")
                    reg.value = 1 if str(state).lower() == "on" else 0
                else:
                    if reg.entity_point == "state":
                        reg.value = entity_data.get("state")
                    else:
                        reg.value = entity_data.get("attributes", {}).get(reg.entity_point)

                result[reg.point_name] = reg.value

            except Exception as e:
                _log.error("Error scraping %s: %s", reg.entity_id, e)

        # pytest expects: {'bool_state': 0} or {'bool_state': 1}
        return result

    # ----------------------------------------
    def get_entity_data(self, entity_id):
        _log.debug(f"HA REQUEST HEADERS = {self._api._headers}")
        _log.debug(
            f"HA REQUEST URL = http://{self.ip_address}:{self.port}/api/states/{entity_id}"
        )
        return self._api.get_state(entity_id)

    # ----------------------------------------
    def parse_config(self, config_dict):
        if config_dict is None:
            return

        for regDef in config_dict:
            if not regDef.get("Entity ID"):
                continue

            read_only = str(regDef.get("Writable", "")).lower() != "true"
            entity_id = regDef["Entity ID"]
            entity_point = regDef["Entity Point"]
            point_name = regDef["Volttron Point Name"]
            units = regDef.get("Units", "")
            reg_type = type_mapping.get(regDef.get("Type", "string"), str)

            reg = HomeAssistantRegister(
                read_only,
                point_name,
                units,
                reg_type,
                regDef.get("Attributes", {}),
                entity_id,
                entity_point,
                description=regDef.get("Notes", "")
            )
            self.insert_register(reg)
