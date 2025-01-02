"""Support for VeoliaIDF."""
from datetime import timedelta, datetime
import json
import logging
import traceback
import asyncio

from pyveoliaidf.client import Client
from pyveoliaidf.enum import PropertyNameEnum
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION, CONF_PASSWORD, CONF_USERNAME, CONF_SCAN_INTERVAL, UnitOfVolume
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_call_later, async_track_time_interval

_LOGGER = logging.getLogger(__name__)

CONF_WEBDRIVER = "webdriver"
CONF_FIREFOX_BINARY_LOCATION = "firefox_binary_location"
CONF_WAITTIME = "wait_time"
CONF_TMPDIR = "tmpdir"
DEFAULT_SCAN_INTERVAL = timedelta(hours=4)
DEFAULT_WAITTIME = 30
ICON_WATER = "mdi:water"

HA_TIME = "time"
HA_TIMESTAMP = "timestamp"
HA_TYPE = "type"
HA_ATTRIBUTION = "Data provided by VeoliaIDF"

VEOLIA_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

HA_PERIOD_START_TIME = "Veolia period start time"
HA_PERIOD_END_TIME = "Veolia period end time"
HA_YESTERDAY_LITER = "Veolia yesterday liter"
HA_TOTAL_LITER = "Veolia total liter"

LAST_INDEX = -1
BEFORE_LAST_INDEX = -2

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_WEBDRIVER): cv.string,
    vol.Required(CONF_FIREFOX_BINARY_LOCATION): cv.string,
    vol.Optional(CONF_WAITTIME, default=DEFAULT_WAITTIME): int,
    vol.Required(CONF_TMPDIR): cv.string,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period
})


# --------------------------------------------------------------------------------------------
async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Configure the platform and add the Linky sensor."""

    _LOGGER.debug("Initializing VeoliaIDF platform...")

    try:
        username = config[CONF_USERNAME]
        _LOGGER.debug(f"username={username}")

        password = config[CONF_PASSWORD]
        _LOGGER.debug("password=***********")

        webdriver = config[CONF_WEBDRIVER]
        _LOGGER.debug(f"webdriver={webdriver}")

        firefox_binary_location = config.get(CONF_FIREFOX_BINARY_LOCATION)
        _LOGGER.debug(f"firefox_binary_location={firefox_binary_location}")

        wait_time = config[CONF_WAITTIME]
        _LOGGER.debug(f"wait_time={wait_time}")

        tmpdir = config[CONF_TMPDIR]
        _LOGGER.debug(f"tmpdir={tmpdir}")

        scan_interval = config[CONF_SCAN_INTERVAL]
        _LOGGER.debug(f"scan_interval={scan_interval}")

        account = VeoliaIDFAccount(hass, username, password, webdriver, firefox_binary_location, wait_time, tmpdir, scan_interval)
        add_entities(account.sensors, True)

        if hass is not None:
            async_call_later(hass, 5, account.async_update_veolia_data)
            async_track_time_interval(hass, account.async_update_veolia_data, account._scan_interval)
        else:
            await account.async_update_veolia_data(None)

        _LOGGER.debug("VeoliaIDF platform initialization has completed successfully")
    except BaseException:
        _LOGGER.error("VeoliaIDF platform initialization has failed with exception : %s", traceback.format_exc())
        raise


# --------------------------------------------------------------------------------------------
class VeoliaIDFAccount:
    """Representation of a VeoliaIDF account."""

    # ----------------------------------
    def __init__(self, hass, username, password, webdriver, firefox_binary_location, wait_time, tmpdir, scan_interval):
        """Initialise the VeoliaIDF account."""
        self._username = username
        self.__password = password
        self._webdriver = webdriver
        self._firefox_binary_location = firefox_binary_location
        self._wait_time = wait_time
        self._tmpdir = tmpdir
        self._scan_interval = scan_interval
        self._data = None
        self.sensors = []

        self.sensors.append(
            VeoliaIDFSensor(HA_PERIOD_START_TIME, PropertyNameEnum.TIME.value, None, BEFORE_LAST_INDEX, self))
        self.sensors.append(
            VeoliaIDFSensor(HA_PERIOD_END_TIME, PropertyNameEnum.TIME.value, None, LAST_INDEX, self))
        self.sensors.append(
            VeoliaIDFSensor(HA_YESTERDAY_LITER, PropertyNameEnum.DAILY_LITER.value, UnitOfVolume.LITERS, LAST_INDEX, self))
        self.sensors.append(
            VeoliaIDFSensor(HA_TOTAL_LITER, PropertyNameEnum.TOTAL_LITER.value, UnitOfVolume.LITERS, LAST_INDEX, self))

    # ----------------------------------
    async def async_update_veolia_data(self, event_time):
        """Fetch new state data for the sensor."""

        _LOGGER.debug("Querying PyVeoliaIDF library for new data...")

        try:
            client = Client(self._username, self.__password, 10, self._webdriver, self._firefox_binary_location, self._wait_time, self._tmpdir)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, client.update)

            self._data = client.data()
            _LOGGER.debug(f"data={json.dumps(self._data, indent=2)}")

            _LOGGER.debug("New data have been retrieved successfully from PyVeoliaIDF library")
        except BaseException:
            _LOGGER.error("Failed to query PyVeoliaIDF library with exception : %s", traceback.format_exc())
            if event_time is None:
                raise

        if event_time is not None:
            for sensor in self.sensors:
                sensor.async_schedule_update_ha_state(True)
            _LOGGER.debug("HA notified that new data is available")

    @property
    def username(self):
        """Return the username."""
        return self._username

    @property
    def webdriver(self):
        """Return the webdriver."""
        return self._webdriver

    @property
    def tmpdir(self):
        """Return the tmpdir."""
        return self._tmpdir

    @property
    def data(self):
        """Return the data."""
        return self._data


class VeoliaIDFSensor(Entity):
    """Representation of a sensor entity for Linky."""

    def __init__(self, name, identifier, unit, index, account: VeoliaIDFAccount):
        """Initialize the sensor."""
        self._name = name
        self._identifier = identifier
        self._unit = unit
        self._index = index
        self.__account = account
        self._username = account.username
        self.__timestamp = None
        self.__measure = None
        self.__type = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.__measure

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_WATER

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_ATTRIBUTION: HA_ATTRIBUTION,
            HA_TIMESTAMP: self.__timestamp,
            HA_TYPE: self.__type,
            CONF_USERNAME: self._username
        }

    def update(self):
        """Retrieve the new data for the sensor."""

        _LOGGER.debug("HA requests its data to be updated...")
        try:
            if self.__account.data is not None:
                data = self.__account.data[self._index]
                if self._unit is not None:
                    # data is a measure in a given unit
                    self.__measure = data[self._identifier]
                else:
                    # data is a date with GAZPAR_DATE_FORMAT
                    self.__measure = datetime.strptime(data[self._identifier], VEOLIA_DATETIME_FORMAT)
                self.__timestamp = data[PropertyNameEnum.TIMESTAMP.value]
                self.__type = data[PropertyNameEnum.TYPE.value]
                _LOGGER.debug("HA data have been updated successfully")
            else:
                _LOGGER.debug("No data available yet for update")
        except BaseException:
            _LOGGER.error("Failed to update HA data with exception : %s", traceback.format_exc())
