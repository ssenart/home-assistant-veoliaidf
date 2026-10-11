"""Offline tests: no network and no browser. The Veolia client is replaced by a fake."""
import asyncio
from unittest import mock

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfVolume

from custom_components.veoliaidf import sensor
from custom_components.veoliaidf.sensor import (
    CONF_PASSWORD,
    CONF_USERNAME,
    HA_TIMESTAMP,
    HA_TYPE,
    HA_TOTAL_LITER,
    LAST_N_DAYS,
    REMOVED_OPTIONS,
)

USERNAME = "user@example.com"

BASE_CONFIG = {
    "platform": "veoliaidf",
    CONF_USERNAME: USERNAME,
    CONF_PASSWORD: "secret",
}

# The options of the browser-based versions, as an existing configuration still has them.
LEGACY_OPTIONS = {
    "webdriver": "/config/drivers/geckodriver",
    "firefox_binary_location": "/usr/bin/firefox",
    "wait_time": 30,
    "tmpdir": "/tmp",
}

RECORDS = [
    {"time": "2026-10-02 21:00:00", "total_liter": 1000, "daily_liter": 10, "type": "Mesuré", "timestamp": "2026-10-04T10:00:00"},
    {"time": "2026-10-03 21:00:00", "total_liter": 1010, "daily_liter": 10, "type": "Mesuré", "timestamp": "2026-10-04T10:00:00"},
]


class FakeClient:
    """Stands in for pyveoliaidf.Client: an async context manager that remembers how it was built and used."""

    last_args = None
    last_kwargs = None
    updates = 0
    closed = 0

    def __init__(self, *args, **kwargs):
        FakeClient.last_args = args
        FakeClient.last_kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        FakeClient.closed += 1

    async def update(self):
        FakeClient.updates += 1

    def data(self):
        return list(RECORDS)


class FailingClient(FakeClient):
    async def update(self):
        raise RuntimeError("the site is down")


def _setup(config, client_class=FakeClient):
    """Run the platform setup with the fake client and return the entities it added."""
    entities = []
    with mock.patch.object(sensor, "Client", client_class):
        asyncio.run(sensor.async_setup_platform(None, config, lambda new_entities, update_before_add: entities.extend(new_entities)))
    return entities


def _validated_config(**overrides):
    return sensor.PLATFORM_SCHEMA({**BASE_CONFIG, **overrides})


def test_the_client_is_built_with_the_credentials_and_the_window_only():
    entities = _setup(_validated_config())

    assert len(entities) == 4
    # No browser option, and no session: the library makes its own, which trusts the Veolia certificate chain.
    assert FakeClient.last_args == (USERNAME, "secret", LAST_N_DAYS)
    assert FakeClient.last_kwargs == {}


def test_the_client_is_used_as_a_context_manager_so_its_session_is_closed():
    closed = FakeClient.closed

    _setup(_validated_config())

    assert FakeClient.closed == closed + 1


def test_a_failed_first_update_is_raised():
    try:
        _setup(_validated_config(), FailingClient)
    except RuntimeError as error:
        assert "the site is down" in str(error)
    else:
        raise AssertionError("the failure was swallowed")


def test_the_options_of_the_browser_versions_are_accepted_and_dropped():
    config = _validated_config(**LEGACY_OPTIONS)

    for option in REMOVED_OPTIONS:
        assert option not in config
    assert len(_setup(config)) == 4


def test_the_configuration_needs_no_browser_option():
    config = _validated_config()

    assert all(option not in config for option in REMOVED_OPTIONS)


def test_sensors_expose_timestamp_and_type_without_username():
    entities = _setup(_validated_config())
    total = next(e for e in entities if e.name == HA_TOTAL_LITER)

    total.update()

    assert total.state == 1010
    attributes = total.extra_state_attributes
    assert attributes[HA_TIMESTAMP] == "2026-10-04T10:00:00"
    assert attributes[HA_TYPE] == "Mesuré"
    assert CONF_USERNAME not in attributes
    assert USERNAME not in str(attributes)


def test_sensors_have_no_state_before_first_update():
    entities = _setup(_validated_config())

    assert all(e.state is None for e in entities)


def test_unique_ids_are_distinct_and_stable():
    first = [e.unique_id for e in _setup(_validated_config())]
    second = [e.unique_id for e in _setup(_validated_config())]

    assert len(set(first)) == 4
    assert first == second


def test_total_sensor_is_a_water_meter_for_the_energy_dashboard():
    entities = _setup(_validated_config())
    total = next(e for e in entities if e.name == HA_TOTAL_LITER)

    assert total.device_class == SensorDeviceClass.WATER
    assert total.state_class == SensorStateClass.TOTAL_INCREASING
    assert total.native_unit_of_measurement == UnitOfVolume.LITERS


def test_other_sensors_are_not_water_meters():
    entities = _setup(_validated_config())
    others = [e for e in entities if e.name != HA_TOTAL_LITER]

    assert len(others) == 3
    for entity in others:
        assert getattr(entity, "state_class", None) is None
        assert getattr(entity, "device_class", None) is None
