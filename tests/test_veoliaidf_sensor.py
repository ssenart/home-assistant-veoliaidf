from custom_components.veoliaidf.sensor import async_setup_platform
from custom_components.veoliaidf.sensor import CONF_USERNAME, CONF_PASSWORD, CONF_WAITTIME, CONF_TMPDIR, CONF_SCAN_INTERVAL, CONF_WEBDRIVER, CONF_FIREFOX_BINARY_LOCATION
import os
import logging
import json
import pytest


# --------------------------------------------------------------------------------------------
class TestVeoliaIDFSensor:

    logger = logging.getLogger(__name__)

    _entities = []

    # ----------------------------------
    def add_entities(self, entities: list, flag: bool):
        self._entities.extend(entities)

    # ----------------------------------
    @pytest.mark.asyncio
    async def test_live(self):

        config = {
            CONF_USERNAME: os.environ["VEOLIAIDF_USERNAME"],
            CONF_PASSWORD: os.environ["VEOLIAIDF_PASSWORD"],
            CONF_WEBDRIVER: "./drivers/geckodriver.exe" if os.name == "nt" else "./drivers/geckodriver",
            CONF_FIREFOX_BINARY_LOCATION: "C:/Program Files/Mozilla Firefox/firefox.exe" if os.name == "nt" else "/usr/bin/firefox",
            CONF_WAITTIME: 30,
            CONF_TMPDIR: "./tmp",
            CONF_SCAN_INTERVAL: 600,
        }

        await async_setup_platform(None, config, self.add_entities)

        for entity in self._entities:
            entity.update()
            state = entity.state
            attributes = entity.device_state_attributes

            TestVeoliaIDFSensor.logger.info(f"state={state}")
            TestVeoliaIDFSensor.logger.info(f"attributes={json.dumps(attributes, indent=2)}")
