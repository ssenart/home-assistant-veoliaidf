from custom_components.veoliaidf.sensor import async_setup_platform
from custom_components.veoliaidf.sensor import CONF_USERNAME, CONF_PASSWORD, CONF_WAITTIME, CONF_TMPDIR, CONF_SCAN_INTERVAL, CONF_WEBDRIVER, CONF_FIREFOX_BINARY_LOCATION, HA_TIMESTAMP
import os
import logging
import json
import pytest


# --------------------------------------------------------------------------------------------
class TestVeoliaIDFSensor:

    logger = logging.getLogger(__name__)

    # ----------------------------------
    @pytest.mark.live
    @pytest.mark.asyncio
    async def test_live(self):

        config = {
            CONF_USERNAME: os.environ["VEOLIAIDF_USERNAME"],
            CONF_PASSWORD: os.environ["VEOLIAIDF_PASSWORD"],
            CONF_WEBDRIVER: None,  # found or downloaded by Selenium Manager
            CONF_FIREFOX_BINARY_LOCATION: "C:/Program Files/Mozilla Firefox/firefox.exe" if os.name == "nt" else "/usr/bin/firefox",
            CONF_WAITTIME: 30,
            CONF_TMPDIR: "./tmp",
            CONF_SCAN_INTERVAL: 600,
        }

        entities = []
        await async_setup_platform(None, config, lambda new_entities, update_before_add: entities.extend(new_entities))

        assert len(entities) == 4

        for entity in entities:
            entity.update()
            attributes = entity.extra_state_attributes

            TestVeoliaIDFSensor.logger.info(f"state={entity.state}")
            TestVeoliaIDFSensor.logger.info(f"attributes={json.dumps(attributes, indent=2)}")

            assert entity.state is not None, f"{entity.name} has no state"
            assert attributes[HA_TIMESTAMP] is not None, f"{entity.name} has no timestamp"
