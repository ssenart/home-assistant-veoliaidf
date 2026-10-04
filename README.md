# Home Assistant Veolia Ile-de-France

Veoliaidf permits to integrate in Home Assistant all your water consumption data.

This custom component is using PyVeoliaIDF library to retrieve Veolia data.
PyVeoliaIDF library relies on Selenium and geckodriver application (see https://github.com/ssenart/PyVeoliaIDF for details).

1. Copy the veoliaidf directory in HA config/custom_components directory.

2. Optional: copy a specific Selenium geckodriver binary in HA config/drivers directory, and set its path in the `webdriver` option below. Ensure it has the execution permission from the runtime environment HA is running on. Geckodriver releases are available here : https://github.com/mozilla/geckodriver/releases. If `webdriver` is omitted, Selenium Manager finds or downloads the geckodriver matching your system (this needs internet access on the first run).

3. Install a compatible version Firefox on HA host. Ensure this version is in the PATH and HA can run it.

4. Update your HA configuration with :

```yaml
sensor:
- platform: veoliaidf
    username: ***
    password: !secret veolia_password
    webdriver: /config/drivers/geckodriver
    firefox_binary_location: /usr/bin/firefox
    tmpdir: /tmp
    scan_interval: 08:00:00
```

Keep the password in HA `secrets.yaml`, as `veolia_password: ***`, so it stays out of your configuration.

5. Restart your HA application. In HA development panel, you should see the new Veolia entities :
- sensor.veolia_total_liter
- sensor.veolia_yesterday_liter
- sensor.veolia_period_start_time
- sensor.veolia_period_end_time

6. Optional: to follow your water consumption in the Energy dashboard, go to Settings → Dashboards → Energy, add a water source and select `sensor.veolia_total_liter`. Home Assistant records long-term statistics from the moment it starts reading this sensor; past readings are not imported.

# Development

The development environment is managed with [uv](https://docs.astral.sh/uv/), from `pyproject.toml` and `uv.lock`. It needs Python 3.14.2 or newer, the version Home Assistant requires.

```bash
cd /path/to/home-assistant-veoliaidf
uv sync                                  # create .venv and install the locked dependencies
uv run flake8 custom_components tests    # lint
```

The development environment pins PyVeoliaIDF `0.4.6a1`, the pre-release on PyPI (see `pyproject.toml`). Once 0.4.6 is final, change the pin to `pyveoliaidf>=0.4.6` and run `uv lock`.

`uv run pytest` runs the offline tests: no network and no browser.

The live test `tests/test_veoliaidf_sensor.py::test_live` is marked `live`, because it logs into the Veolia web site with your account. Put `VEOLIAIDF_USERNAME` and `VEOLIAIDF_PASSWORD` in a `.env` file (do not commit it), then run:

```bash
uv run --env-file .env pytest -m live
```

# Note about using geckodriver in a Docker container

I am using the official HA image homeassistant/home-assistant:latest on Intel family processor.
HA image is based on Alpine Linux distribution. The corresponding Alpine Hardware Architecture for me is x86_64 (see wiki.alpinelinux.org/wiki/Architecture).
I'm using the geckodriver built for this architecture exactly :
- See the geckodriver releases by architecture here : https://github.com/mozilla/geckodriver/releases.
- For HassIO users, refer the next note in this document.

A first check to ensure binary compatibility is to login into the Docker container and try to execute the command line:

```bash
/config/drivers/geckodriver --version
```

You should see something like :

```bash
geckodriver <version> (<commit> <build date>)

The source code of this program is available from
testing/geckodriver in https://hg.mozilla.org/mozilla-central.

This program is subject to the terms of the Mozilla Public License 2.0.
You can obtain a copy of the license at https://mozilla.org/MPL/2.0/.
```

If you don't, two possible reasons :
1. Execution permission of the file is wrongly set. Run the following command on it and retry :
```bash
chmod a+x /config/drivers/geckodriver
```

2. Binary format of the file is not compatible. Double check what kind of binary your need depending on your processor architecture.

After geckodriver version has been found and validated, you have to install a compatible Firefox version in your Docker container. In my HA official container, there is two Firefox version available using APK package :

```bash
apk list | grep firefox
```

```bash
firefox-esr-78.6.1-r0 x86_64 {firefox-esr} (GPL-3.0-only AND LGPL-2.1-only AND LGPL-3.0-only AND MPL-2.0)
firefox-84.0.2-r0 x86_64 {firefox} (GPL-3.0-only AND LGPL-2.1-only AND LGPL-3.0-only AND MPL-2.0) [installed]
```

I tried both, but only firefox-84.0.2-r0 is working fine. The command line to install it is :

```bash
apk install firefox
```

Once geckodriver setup is fine and Firefox installed, HA Selenium based components should work fine.

# Note about using geckodriver in HassIO/RaspberryPi distribution

Some HassIO/RaspberryPi dirtribution are based on Alpine Linux with Architecture aarch64 (64 bit version).

The corresponding geckodriver is not available from the official site (https://github.com/mozilla/geckodriver/releases) and I had to recompile a dedicated version available here (from source code available here : https://hg.mozilla.org/mozilla-central/file and instructions here : https://firefox-source-docs.mozilla.org/testing/geckodriver/Building.html): 


https://github.com/ssenart/ha-custom_components/blob/master/drivers/geckodriver-0.29.0-0-aarch64.tgz


This version is compatible with firefox-84.x.
But, it is not compatible with firefox-esr-78.x.

You can install the corresponding firefox package with the command :

```bash
apk add firefox
```
