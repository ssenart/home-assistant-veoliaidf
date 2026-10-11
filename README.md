# Home Assistant Veolia Ile-de-France

Veoliaidf permits to integrate in Home Assistant all your water consumption data.

This custom component is using PyVeoliaIDF library to retrieve Veolia data.
PyVeoliaIDF reads the data over HTTPS from the Veolia customer area: it needs no browser and no web driver (see https://github.com/ssenart/PyVeoliaIDF for details).

1. Copy the veoliaidf directory in HA config/custom_components directory.

2. Update your HA configuration with :

```yaml
sensor:
- platform: veoliaidf
    username: ***
    password: !secret veolia_password
    scan_interval: 08:00:00
```

Keep the password in HA `secrets.yaml`, as `veolia_password: ***`, so it stays out of your configuration.

The options `webdriver`, `firefox_binary_location`, `wait_time` and `tmpdir` of the previous versions are no longer used. An existing configuration that still has them keeps working: Home Assistant logs a warning and ignores them. You can remove them, and uninstall Firefox and geckodriver if you installed them only for this component.

3. Restart your HA application. In HA development panel, you should see the new Veolia entities :
- sensor.veolia_total_liter
- sensor.veolia_yesterday_liter
- sensor.veolia_period_start_time
- sensor.veolia_period_end_time

4. Optional: to follow your water consumption in the Energy dashboard, go to Settings → Dashboards → Energy, add a water source and select `sensor.veolia_total_liter`. Home Assistant records long-term statistics from the moment it starts reading this sensor; past readings are not imported.

# Development

The development environment is managed with [uv](https://docs.astral.sh/uv/), from `pyproject.toml` and `uv.lock`. It needs Python 3.14.2 or newer, the version Home Assistant requires.

```bash
cd /path/to/home-assistant-veoliaidf
uv sync                                  # create .venv and install the locked dependencies
uv run flake8 custom_components tests    # lint
```

The development environment installs PyVeoliaIDF from the sibling checkout `../PyVeoliaIDF` (see `tool.uv.sources` in `pyproject.toml`), because the asynchronous version is not on PyPI yet. Once it is released, pin it there (for instance `pyveoliaidf>=0.5.0`), remove the source and run `uv lock`. `custom_components/veoliaidf/manifest.json` already requires `pyveoliaidf==0.5.0a1`: set it to the version that is actually published.

`uv run pytest` runs the offline tests: no network and no browser.

The live test `tests/test_veoliaidf_sensor.py::test_live` is marked `live`, because it logs into the Veolia web site with your account. Put `VEOLIAIDF_USERNAME` and `VEOLIAIDF_PASSWORD` in a `.env` file (do not commit it), then run:

```bash
uv run --env-file .env pytest -m live
```
