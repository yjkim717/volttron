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

# === Handlers ===
from device_handlers.light_handler import LightHandler
from device_handlers.switch_handler import SwitchHandler
from device_handlers.climate_handler import ClimateHandler

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
# Home Assistant Register
# =====================================================
class HomeAssistantRegister(BaseRegister):
    def __init__(
        self, read_only, pointName, units, reg_type,
        attributes, entity_id, entity_point,
        default_value=None, description=''
    ):
        super(HomeAssistantRegister, self).__init__("byte", read_only, pointName, units, description)
        self.reg_type = reg_type
        self.attributes = attributes
        self.entity_id = entity_id
        self.entity_point = entity_point
        self.value = default_value


# =====================================================
# Interface Class
# =====================================================
class Interface(BasicRevert, BaseInterface):
    def __init__(self, **kwargs):
        super(Interface, self).__init__(**kwargs)
        self.ip_address = None
        self.access_token = None
        self.port = None
        self.units = None

    # ----------------------------------------
    # Configuration
    # ----------------------------------------
    def configure(self, config_dict, registry_config_str):
        """Initialize connection info and parse registry."""
        self.ip_address = config_dict.get("ip_address")
        self.access_token = config_dict.get("access_token")
        self.port = config_dict.get("port")

        if not all([self.ip_address, self.access_token, self.port]):
            raise ValueError("ip_address, access_token, and port must be set in driver configuration")

        self.parse_config(registry_config_str)

    # ----------------------------------------
    # Read a point
    # ----------------------------------------
    def get_point(self, point_name):
        register = self.get_register_by_name(point_name)
        entity_data = self.get_entity_data(register.entity_id)
        if register.point_name == "state":
            return entity_data.get("state", None)
        return entity_data.get("attributes", {}).get(register.point_name, None)

    # ----------------------------------------
    # Write a point (set value)
    # ----------------------------------------
    def _set_point(self, point_name, value):
        register = self.get_register_by_name(point_name)
        if register.read_only:
            raise IOError(f"Trying to write to a read-only point: {point_name}")

        register.value = register.reg_type(value)
        entity_id = register.entity_id

        # Get the correct handler for this entity
        handler = self._get_handler(entity_id)
        handler.set_state(register.entity_point, register.value)

        _log.info(f"[SET] {entity_id} → {register.entity_point} = {register.value}")
        return register.value

    # ----------------------------------------
    # Get handler by entity type
    # ----------------------------------------
    def _get_handler(self, entity_id):
        """Factory method that returns appropriate handler instance."""
        if entity_id.startswith("light."):
            return LightHandler(self.ip_address, self.port, self.access_token, entity_id)
        elif entity_id.startswith("switch."):
            return SwitchHandler(self.ip_address, self.port, self.access_token, entity_id)
        elif entity_id.startswith("climate."):
            return ClimateHandler(self.ip_address, self.port, self.access_token, entity_id)
        else:
            raise ValueError(f"Unsupported entity type: {entity_id}")

    # ----------------------------------------
    # Read all device states
    # ----------------------------------------
    def _scrape_all(self):
        result = {}
        all_registers = (
            self.get_registers_by_type("byte", True)
            + self.get_registers_by_type("byte", False)
        )

        for reg in all_registers:
            try:
                entity_data = self.get_entity_data(reg.entity_id)
                if reg.entity_point == "state":
                    reg.value = entity_data.get("state", None)
                else:
                    reg.value = entity_data.get("attributes", {}).get(reg.entity_point, None)
                result[reg.point_name] = reg.value
            except Exception as e:
                _log.error(f"Error scraping {reg.entity_id}: {e}")

        return result

    # ----------------------------------------
    # Retrieve state from Home Assistant API
    # ----------------------------------------
    def get_entity_data(self, entity_id):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        url = f"http://{self.ip_address}:{self.port}/api/states/{entity_id}"

        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        else:
            _log.error(f"Failed to fetch entity data for {entity_id}: {resp.text}")
            raise Exception(f"Error fetching state for {entity_id}")

    # ----------------------------------------
    # Parse registry file (registry_config_str)
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
            type_name = regDef.get("Type", "string")
            reg_type = type_mapping.get(type_name, str)
            attributes = regDef.get("Attributes", {})

            register = HomeAssistantRegister(
                read_only,
                point_name,
                units,
                reg_type,
                attributes,
                entity_id,
                entity_point,
                default_value=None,
                description=regDef.get("Notes", "")
            )

            self.insert_register(register)
