.. _HomeAssistant-Driver:

Home Assistant Driver
=====================

The Home Assistant driver enables VOLTTRON to read any data point from any Home Assistant controlled device.
Control (write access) is supported for multiple device types including lights, climate/thermostats, locks, fans, and sirens.
The driver uses a Factory pattern with specialized handlers for each device type, making it easy to extend support for new device types.

The following diagram shows interaction between platform driver agent and home assistant driver.

.. mermaid::

   sequenceDiagram
       HomeAssistant Driver->>HomeAssistant: Retrieve Entity Data (REST API)
       HomeAssistant-->>HomeAssistant Driver: Entity Data (Status Code: 200)
       HomeAssistant Driver->>PlatformDriverAgent: Publish Entity Data
       PlatformDriverAgent->>Controller Agent: Publish Entity Data

       Controller Agent->>HomeAssistant Driver: Instruct to Control Device
       HomeAssistant Driver->>HandlerFactory: Get Handler for Entity
       HandlerFactory-->>HomeAssistant Driver: Device Handler Instance
       HomeAssistant Driver->>HomeAssistant: Send Device Command (REST API)
       HomeAssistant-->>HomeAssistant Driver: Command Acknowledgement (Status Code: 200)

Architecture
------------

The Home Assistant driver uses a Factory pattern with specialized device handlers:

- **HandlerFactory**: Routes entity_id to appropriate handler based on prefix (light., climate., lock., fan., siren.)
- **BaseDeviceHandler**: Abstract base class providing common functionality
- **Device Handlers**: Specialized handlers for each device type:
  - LightHandler: Controls light on/off
  - ClimateHandler: Controls HVAC mode and temperature
  - LockHandler: Controls lock/unlock
  - FanHandler: Controls fan power, speed, and oscillation
  - SirenHandler: Controls siren on/off

This architecture follows SOLID principles, particularly the Open/Closed Principle (OCP) and Dependency Inversion Principle (DIP),
making it easy to add new device types without modifying existing code.

Architectural Improvements
++++++++++++++++++++++++++

The current architecture represents a significant refactoring from a monolithic design with giant conditional blocks
to a clean, extensible architecture. The following improvements were made:

**Before (Monolithic Design):**
- Single Interface class with 1000+ lines
- Giant if/elif chains for each device type (200+ lines per method)
- Adding new devices required modifying the Interface class
- Difficult to test individual device behaviors
- Violated Single Responsibility Principle

**After (Handler-Based Architecture):**
- Layered architecture with specialized Device Handlers
- Interface class reduced to ~350 lines
- Each Handler manages one device type (Single Responsibility)
- New devices added by registering in Factory (Open/Closed Principle)
- Each Handler independently testable
- Follows SOLID principles

Design Patterns
++++++++++++++

The architecture uses three key design patterns:

**1. Factory Pattern**
   The ``HandlerFactory`` creates appropriate handler instances based on entity_id prefix.
   This centralizes object creation and isolates handler imports.

**2. Strategy Pattern**
   Each device type has its own strategy (handler) for handling state changes.
   The appropriate strategy is selected at runtime based on the entity_id.

**3. Registry Pattern**
   The Factory maintains a registry of device type → handler mappings, allowing for
   dynamic handler lookup and easy extension.

SOLID Principles Applied
++++++++++++++++++++++++

The architecture follows all five SOLID principles:

**1. Single Responsibility Principle (SRP)**
   Each Handler manages only one device type. For example, ``LightHandler`` only handles
   light devices, ``ClimateHandler`` only handles climate devices, etc.

**2. Open/Closed Principle (OCP)**
   The system is open for extension (new handlers can be added) but closed for modification
   (existing code doesn't need to change). New devices are added by registering in the Factory,
   not by modifying the Interface.

**3. Liskov Substitution Principle (LSP)**
   All Handlers implement ``BaseDeviceHandler`` and can be substituted without breaking code.
   Any handler can be used wherever a ``BaseDeviceHandler`` is expected.

**4. Interface Segregation Principle (ISP)**
   Handlers only implement what they need. No forced implementation of unused methods.

**5. Dependency Inversion Principle (DIP)**
   The Interface depends on ``HandlerFactory`` (abstraction), not concrete handler implementations.
   The Factory depends on ``BaseDeviceHandler`` (abstraction), not specific handler classes.

Adding a New Device Type
+++++++++++++++++++++++++

With the new architecture, adding a new device type is straightforward:

**Steps:**
1. Create a new Handler class (e.g., ``NewDeviceHandler``) that inherits from ``BaseDeviceHandler``
2. Register it in ``HandlerFactory._registry``
3. Done! The Interface automatically works with the new handler

**Example:**

.. code-block:: python

   # 1. Create new_device_handler.py
   class NewDeviceHandler(BaseDeviceHandler):
       def set_state(self, entity_point, value):
           # Device-specific logic
           service = "turn_on" if value == 1 else "turn_off"
           self.call_service("new_device", service)

   # 2. Register in factory.py
   self._register("new_device.", NewDeviceHandler, required=False)

   # 3. That's it! Interface automatically works with new handler

**Benefits:**
- Only ~50-100 lines of new code (new file only)
- No modification to existing Interface code
- Easy to test in isolation
- No risk of breaking existing functionality

Pre-requisites
--------------
Before proceeding, find your Home Assistant IP address and long-lived access token from `here <https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token>`_.

Clone the repository, start volttron, install the listener agent, and the platform driver agent.

- `Listener agent <https://volttron.readthedocs.io/en/main/introduction/platform-install.html#installing-and-running-agents>`_
- `Platform driver agent <https://volttron.readthedocs.io/en/main/agent-framework/core-service-agents/platform-driver/platform-driver-agent.html?highlight=platform%20driver%20isntall#configuring-the-platform-driver>`_

Configuration
--------------

After cloning, generate configuration files. Each device requires one device configuration file and one registry file.
Ensure your registry_config parameter in your device configuration file, links to correct registry config name in the
config store. For more details on how volttron platform driver agent works with volttron configuration store see,
`Platform driver configuration <https://volttron.readthedocs.io/en/main/agent-framework/driver-framework/platform-driver/platform-driver.html#configuration-and-installation>`_

Supported device types include:
- **Lights** (light.*): Control on/off state
- **Climate/Thermostats** (climate.*): Control HVAC mode and temperature
- **Locks** (lock.*): Control lock/unlock state
- **Fans** (fan.*): Control power, speed, and oscillation
- **Sirens** (siren.*): Control on/off state

Examples for various device types are provided below.

Device configuration
++++++++++++++++++++

Device configuration file contains the connection details to you home assistant instance and driver_type as "home_assistant"

.. code-block:: json

   {
       "driver_config": {
           "ip_address": "Your Home Assistant IP",
           "access_token": "Your Home Assistant Access Token",
           "port": "Your Port"
       },
       "driver_type": "home_assistant",
       "registry_config": "config://light.example.json",
       "interval": 30,
       "timezone": "UTC"
   }

Registry Configuration
+++++++++++++++++++++++

Registry file can contain one single device and its attributes or a logical group of devices and its
attributes. Each entry should include the full entity id of the device, including the home assistant provided prefix
such as "light.", "climate.", "lock.", "fan.", "siren." etc. The driver uses these prefixes to route to the appropriate
device handler via the HandlerFactory pattern. The driver can control multiple device types (lights, climate, locks, fans, sirens)
and can read data from all devices controlled by home assistant.

Each entry in a registry file should also have a 'Entity Point' and a unique value for 'Volttron Point Name'. The 'Entity ID' maps to the device instance, the 'Entity Point' extracts the attribute or state, and 'Volttron Point Name' determines the name of that point as it appears in VOLTTRON.

Attributes can be located in the developer tools in the Home Assistant GUI.

.. image:: home-assistant.png


.. note::

When using a single registry file to represent a logical group of multiple physical entities, make sure the
"Volttron Point Name" is unique within a single registry file.

For example, if a registry file contains entities with
id  'light.instance1' and 'light.instance2' the entry for the attribute brightness for these two light instances could
have "Volttron Point Name" as 'light1/brightness' and 'light2/brightness' respectively. This would ensure that data
is posted to unique topic names and brightness data from light1 is not overwritten by light2 or vice-versa.

Transfer the registers files and the config files into the VOLTTRON config store using the commands below:

.. code-block:: bash

   vctl config store platform.driver light.example.json HomeAssistant_Driver/light.example.json
   vctl config store platform.driver devices/BUILDING/ROOM/light.example HomeAssistant_Driver/light.example.config

Upon completion, initiate the platform driver. Utilize the listener agent to verify the driver output:

.. code-block:: bash

   2023-09-12 11:37:00,226 (listeneragent-3.3 211531) __main__ INFO: Peer: pubsub, Sender: platform.driver:, Bus: , Topic: devices/BUILDING/ROOM/light.example/all, Headers: {'Date': '2023-09-12T18:37:00.224648+00:00', 'TimeStamp': '2023-09-12T18:37:00.224648+00:00', 'SynchronizedTimeStamp': '2023-09-12T18:37:00.000000+00:00', 'min_compatible_version': '3.0', 'max_compatible_version': ''}, Message:
   [{'light_brightness': 254, 'state': 'on'},
    {'light_brightness': {'type': 'integer', 'tz': 'UTC', 'units': 'int'},
     'state': {'type': 'integer', 'tz': 'UTC', 'units': 'On / Off'}}]

Running Home Assistant with Docker (Required for Integration Tests)
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To fully test the expanded write-access functionality of the Home Assistant Driver
(fans, locks, climate, sirens), the driver must interact with a real Home Assistant instance.

The original VOLTTRON PlatformWrapper is not sufficient because it does not simulate:

- Real REST API endpoints
- Authentication / tokens
- Entity attributes
- Device behavior (brightness, speed, HVAC mode, oscillation, etc.)

Therefore, our project uses a Docker-based Home Assistant server to provide a reproducible and realistic test environment.

Start Home Assistant using Docker
**********************************

Run the following command to start Home Assistant in a Docker container:

.. code-block:: bash

   docker run -d \
     --name homeassistant \
     -p 8123:8123 \
     -v ~/ha-test/config:/config \
     ghcr.io/home-assistant/home-assistant:stable

After a few minutes, Home Assistant will be available at:

   http://localhost:8123

Locate Configuration Directory
******************************

Home Assistant stores all configuration files inside the mounted directory:

- **macOS/Linux**: ``~/ha-test/config``

Important files include:

- ``configuration.yaml``
- ``home-assistant.log``
- ``.storage/`` (stores UI-created helpers and entities)

Add Test Entities
*****************

The driver tests require a set of Home Assistant entities for lights, locks, climate devices, fans, and sirens.

In our setup, all test devices except the siren were created through the Home Assistant UI, which stores them under the .storage/ directory automatically.
Only the siren entity requires a template entry in configuration.yaml.

.. list-table:: Required Test Entities
   :header-rows: 1
   :widths: 30 30 40

   * - Device Type
     - Test Entity ID
     - Creation Method
   * - Light
     - ``light.test_light``
     - Created through Home Assistant UI (Helper → Light)
   * - Lock
     - ``lock.test_lock``
     - Created through Home Assistant UI (Helper → Lock)
   * - Climate
     - ``climate.test_climate``
     - Created through Home Assistant UI (Helper → Climate)
   * - Fan
     - ``fan.test_fan``
     - Created through Home Assistant UI (Helper → Fan)
   * - Siren
     - ``siren.test_siren``
     - Created using a template siren (requires YAML)

Example: Template Siren (added to configuration.yaml)
======================================================

Home Assistant does not provide a built-in UI helper for creating siren entities.
Therefore, the siren used in our test suite is defined via a template siren that wraps an input_boolean.

Add the following to your configuration.yaml:

.. code-block:: yaml

   siren:
     - platform: template
       sirens:
         test_siren:
           friendly_name: "Test Siren"
           value_template: "{{ states('input_boolean.test_siren_switch') }}"
           turn_on:
             service: input_boolean.turn_on
             target:
               entity_id: input_boolean.test_siren_switch
           turn_off:
             service: input_boolean.turn_off
             target:
               entity_id: input_boolean.test_siren_switch

Restart Home Assistant to apply changes:

.. code-block:: bash

   docker restart homeassistant

Why Docker Is Required
***********************

The legacy PlatformWrapper used in previous semesters does not expose real
Home Assistant behavior — no attributes, no REST API, no entity registry —
making it impossible to test write-access for new device types such as locks,
fans, and sirens. Docker provides an actual running Home Assistant environment
with real state transitions and entity attributes.

Docker provides:

- A stable, reproducible Home Assistant environment
- Real entity states & REST API responses
- Real attribute changes (brightness, mode, speed, oscillate, lock state)
- Valid end-to-end testing for all device handlers

Without Docker, only light/climate can be partially simulated, and locks/fans/sirens cannot be tested realistically.

Running Tests
+++++++++++++++++++++++

All test entities (except the siren) are created through the Home Assistant UI,
so the corresponding entities automatically appear under the .storage/ directory.
The siren entity is configured via configuration.yaml as described above.

These tests require a running Home Assistant instance (Docker-based setup described above).

To run tests on the VOLTTRON home assistant driver, you need to set up test entities in your Home Assistant instance:

1. Create a toggle helper: **Settings > Devices & services > Helpers > Create Helper > Toggle**. Name it **volttrontest**.
2. Create test entities for various device types:
   - Light: ``light.test_light``
   - Lock: ``lock.test_lock``
   - Climate: ``climate.test_climate``
   - Fan: ``fan.test_fan``
   - Siren: ``input_boolean.test_siren_switch`` (uses input_boolean as siren for testing)

After setting up the test entities, run pytest from the root of your VOLTTRON directory:

.. code-block:: bash
    pytest services/core/PlatformDriverAgent/tests/test_home_assistant.py

The test suite includes integration tests for:
- Input boolean devices (3 tests)
- Light handler (3 tests)
- Lock handler (5 tests)
- Climate handler (3 tests)
- Fan handler (5 tests, 1 may be skipped if oscillation is not supported)
- Siren handler (5 tests)

If everything works correctly, you should see approximately 20+ passed tests (some may be skipped depending on device capabilities).
