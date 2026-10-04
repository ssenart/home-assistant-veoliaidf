"""Offline tests: no network and no browser. The Veolia client is replaced by a fake."""
import asyncio
from unittest import mock

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfVolume

from custom_components.veoliaidf import sensor
from custom_components.veoliaidf.sensor import (
    CONF_FIREFOX_BINARY_LOCATION,
    CONF_PASSWORD,
    CONF_TMPDIR,
    CONF_USERNAME,
    CONF_WEBDRIVER,
    HA_TIMESTAMP,
    HA_TYPE,
    HA_TOTAL_LITER,
)

USERNAME = "user@example.com"

BASE_CONFIG = {
    "platform": "veoliaidf",
    CONF_USERNAME: USERNAME,
    CONF_PASSWORD: "secret",
    CONF_FIREFOX_BINARY_LOCATION: "/usr/bin/firefox",
    CONF_TMPDIR: "/tmp",
}

RECORDS = [
    {"time": "2026-10-02 21:00:00", "total_liter": "1000", "daily_liter": "10", "type": "Mesuré", "timestamp": "2026-10-04T10:00:00"},
    {"time": "2026-10-03 21:00:00", "total_liter": "1010", "daily_liter": "10", "type": "Mesuré", "timestamp": "2026-10-04T10:00:00"},
]


class FakeClient:
    """Stands in for pyveoliaidf.client.Client and remembers the arguments it was built with."""

    last_args = None

    def __init__(self, *args, **kwargs):
        FakeClient.last_args = args

    def update(self):
        pass

    def data(self):
        return list(RECORDS)


def _setup(config):
    """Run the platform setup with the fake client and return the entities it added."""
    entities = []
    with mock.patch.object(sensor, "Client", FakeClient):
        asyncio.run(sensor.async_setup_platform(None, config, lambda new_entities, update_before_add: entities.extend(new_entities)))
    return entities


def _validated_config(**overrides):
    return sensor.PLATFORM_SCHEMA({**BASE_CONFIG, **overrides})


def test_webdriver_is_optional_and_passed_as_none():
    entities = _setup(_validated_config())

    assert len(entities) == 4
    # Client(username, password, last_n_days, webdriver, ...): no webdriver means Selenium Manager.
    assert FakeClient.last_args[3] is None


def test_explicit_webdriver_is_passed_through():
    _setup(_validated_config(**{CONF_WEBDRIVER: "/config/drivers/geckodriver"}))

    assert FakeClient.last_args[3] == "/config/drivers/geckodriver"


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
