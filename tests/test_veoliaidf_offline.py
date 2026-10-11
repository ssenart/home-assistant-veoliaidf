"""Offline tests: no network and no browser. The Veolia client is replaced by a fake."""
import asyncio
from datetime import date, datetime, time
from decimal import Decimal
from unittest import mock

from pyveoliaidf import ConsumptionHistory, Reading, Step

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
    to_rows,
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


def reading(day, volume, index, estimated=False):
    """A reading of the library: volumes and indexes are Decimal cubic meters."""

    return Reading(
        day=day,
        time=datetime.combine(day, time(21)),
        volume_m3=Decimal(volume),
        index_m3=Decimal(index),
        estimated=estimated,
    )


def history(*readings):
    return ConsumptionHistory(
        contract_number="C",
        meter_number="X1",
        point_id="1",
        step=Step.DAY,
        start=date(2026, 10, 1),
        end=date(2026, 10, 4),
        period_start=None,
        period_end=None,
        readings=list(readings),
        meter_readings=[],
        average_price_eur_m3=None,
        permanent_flow_threshold=None,
        shows_permanent_flow=False,
        can_compare_month=False,
        retrieved_at=datetime(2026, 10, 4, 10, 0),
    )


HISTORY = history(reading(date(2026, 10, 2), "0.010", "1.000"), reading(date(2026, 10, 3), "0.010", "1.010", estimated=True))


class FakeClient:
    """Stands in for pyveoliaidf.Client: an async context manager that remembers how it was built and used."""

    last_args = None
    last_kwargs = None
    last_history_kwargs = None
    closed = 0

    def __init__(self, *args, **kwargs):
        FakeClient.last_args = args
        FakeClient.last_kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        FakeClient.closed += 1

    async def history(self, **kwargs):
        FakeClient.last_history_kwargs = kwargs
        return HISTORY


class FailingClient(FakeClient):
    async def history(self, **kwargs):
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
    assert FakeClient.last_args == (USERNAME, "secret")
    assert FakeClient.last_kwargs == {}
    assert FakeClient.last_history_kwargs == {"last_n_days": LAST_N_DAYS}


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
    assert attributes[HA_TYPE] == "Estimé"
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


def test_rows_convert_the_readings_of_the_library():
    rows = to_rows(HISTORY)

    assert rows == [
        {"time": "2026-10-02 21:00:00", "total_liter": 1000, "daily_liter": 10, "type": "Mesuré", "timestamp": "2026-10-04T10:00:00"},
        {"time": "2026-10-03 21:00:00", "total_liter": 1010, "daily_liter": 10, "type": "Estimé", "timestamp": "2026-10-04T10:00:00"},
    ]


def test_rows_keep_the_liter_precision_of_the_site():
    rows = to_rows(history(reading(date(2026, 10, 2), "0.374", "144.242")))

    assert (rows[0]["total_liter"], rows[0]["daily_liter"]) == (144242, 374)


def test_no_readings_give_no_rows():
    assert to_rows(history()) == []
