# Home Assistant Veolia Ile-de-France

Veoliaidf permits to integrate in Home Assistant all your water consumption data.

This custom component is using pyveoliaidf library to retrieve Veolia data.
pyveoliaidf reads the data over HTTPS from the Veolia customer area: it needs no browser and no web driver (see https://github.com/ssenart/pyveoliaidf for details).

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

# Reporting an issue
Something does not work? Please open an issue at https://github.com/ssenart/home-assistant-veoliaidf/issues. If the cause is in the Veolia data itself (a login error, a missing reading, an `UnexpectedResponseError`), it will be moved to the [pyveoliaidf library](https://github.com/ssenart/pyveoliaidf#reporting-an-issue), which explains in detail how to report.

## First, check these
1. **Does the website work?** Log in at https://connexion.leaudiledefrance.fr and open your consumption history. If it fails there too, it is not the component.
2. **Are you up to date?** Update the component (HACS or a new copy of `custom_components/veoliaidf`) and restart Home Assistant. The site changes, and the fix may be released already: see the [changelog](CHANGELOG.md).
3. **Did you migrate?** The options `webdriver`, `firefox_binary_location`, `wait_time` and `tmpdir` are no longer used. Home Assistant warns about them and ignores them: you can remove them.

## What to include
* What happened and what you expected; since when it stopped working, if it worked.
* The **Home Assistant version** and how it is installed (OS, Container, Core, Supervised), and the **component version** (`manifest.json`) with the **pyveoliaidf version** (Settings, System, Logs show it when the component loads, or `pip show pyveoliaidf` in the Home Assistant environment).
* Your configuration **without the password and the login**:

  ```yaml
  sensor:
    - platform: veoliaidf
      username: XXX
      password: XXX
      scan_interval: 08:00:00
  ```
* The **complete error** from Settings, System, Logs, with its traceback.
* The **debug log**. Add this to `configuration.yaml`, restart, wait for the next update (or restart again), and copy the lines that mention `veoliaidf`:

  ```yaml
  logger:
    default: warning
    logs:
      custom_components.veoliaidf: debug
      pyveoliaidf: debug
  ```

  The debug log of the library shows each call (method, path, status, duration) and each retry, and never your password, tokens or the answers of the site. The component itself logs, at the debug level, **your login** (`username=...`), the masked password, and the readings it received (your consumption). Replace your login with `XXX` before you post.
* The **shape** of your account, for instance "1 contract, 1 meter".
* Whether it happens **always, sometimes or once**, and the time of the last failure.

## Check what you share
Replace with `XXX` before you post: your password, your login (mail), contract and meter numbers, names, addresses, phone numbers, and any long random identifier. Never post tokens, cookies or `sid` values. The versions, the error messages, the status codes and your consumption values are safe to share.

# Development

The development environment is managed with [uv](https://docs.astral.sh/uv/), from `pyproject.toml` and `uv.lock`. It needs Python 3.14.2 or newer, the version Home Assistant requires.

```bash
cd /path/to/home-assistant-veoliaidf
uv sync                                  # create .venv and install the locked dependencies
uv run flake8 custom_components tests    # lint
```

The development environment installs the pre-release `pyveoliaidf==0.5.0a1` from PyPI (see `pyproject.toml`), the same version that `custom_components/veoliaidf/manifest.json` requires. To test against a local checkout of the library instead, add `[tool.uv.sources]` with `pyveoliaidf = { path = "../pyveoliaidf", editable = true }` and run `uv lock`, but do not commit it. When a new version of the library is released, change the pin in both files and run `uv lock`.

`uv run pytest` runs the offline tests: no network and no browser.

The live test `tests/test_veoliaidf_sensor.py::test_live` is marked `live`, because it logs into the Veolia web site with your account. Put `VEOLIAIDF_USERNAME` and `VEOLIAIDF_PASSWORD` in a `.env` file (do not commit it), then run:

```bash
uv run --env-file .env pytest -m live
```
