# Home Assistant Veolia Ile-de-France

A Home Assistant custom integration that reads the water consumption of your **Veolia Ile-de-France** account (L'eau d'Île-de-France / SEDIF) and gives it as sensors: yesterday's consumption in liters, the index of your water meter (usable in the **Energy dashboard**), and the period it covers.

Veolia's water meters are wireless and send the consumption once a day, so the data is refreshed daily: the integration is not a live flow meter.

> **Unofficial.** Veolia offers no public API. The integration uses the [pyveoliaidf](https://github.com/ssenart/pyveoliaidf) library, which reads the same backend as the Veolia customer area website. A change on their side may break it: see [Limitations](#limitations).

**Contents**
[What you get](#what-you-get) ·
[Requirements](#requirements) ·
[Installation](#installation) ·
[Configuration](#configuration) ·
[First start](#first-start) ·
[Entities](#entities) ·
[Energy dashboard](#energy-dashboard) ·
[Examples](#examples) ·
[Upgrading](#upgrading-from-a-version-that-needed-firefox) ·
[Troubleshooting](#troubleshooting) ·
[Limitations](#limitations) ·
[Reporting an issue](#reporting-an-issue) ·
[Development](#development)

## What you get

| Entity | State | |
|---|---|---|
| `sensor.veolia_yesterday_liter` | The consumption of the last day, in liters | |
| `sensor.veolia_total_liter` | The index of the water meter, in liters | A water meter for the **Energy dashboard** |
| `sensor.veolia_period_start_time` | The time of the previous reading | |
| `sensor.veolia_period_end_time` | The time of the latest reading | |

## Requirements
* **A Veolia Ile-de-France account** with a remote-reading meter, and its login and password: the ones you use on https://connexion.leaudiledefrance.fr. Check that you can see your consumption history there.
* **Home Assistant** with access to the internet. It is developed and tested with Home Assistant 2026.9.
* Nothing else: **no browser, no Firefox, no geckodriver**. Home Assistant installs the Python library that the integration needs (`pyveoliaidf`, from PyPI) by itself, the first time it starts the integration, so it needs access to PyPI then.

## Installation

### With HACS (recommended)
[HACS](https://hacs.xyz/) installs the integration and tells you when there is an update.

1. In Home Assistant, open **HACS**, then the menu (three dots, top right), then **Custom repositories**.
2. Enter `https://github.com/ssenart/home-assistant-veoliaidf` as the repository, choose the type **Integration**, and click **Add**.
3. Search for **Veolia Ile-de-France** in HACS, open it, and click **Download**. To try a pre-release (an alpha or a beta), turn on **Show beta versions** in the download dialog.
4. **Restart Home Assistant** (Settings, System, the power menu, Restart).
5. Go on with [Configuration](#configuration).

### Manually
1. Download the latest release from https://github.com/ssenart/home-assistant-veoliaidf/releases (or clone the repository).
2. Copy the folder `custom_components/veoliaidf` into the `custom_components` folder of your Home Assistant configuration. That is the folder that holds `configuration.yaml` (`/config` in Home Assistant OS and in the container). You can reach it with the **File editor**, **Studio Code Server** or **Samba share** add-on, or over SSH. Create `custom_components` if it does not exist.
3. You should end up with:

   ```
   config/
   ├── configuration.yaml
   ├── secrets.yaml
   └── custom_components/
       └── veoliaidf/
           ├── __init__.py
           ├── manifest.json
           └── sensor.py
   ```
4. **Restart Home Assistant**, then go on with [Configuration](#configuration).

## Configuration
The integration is configured in YAML. There is no screen in Settings, Devices & services to add it.

1. **Keep your password in `secrets.yaml`**, next to `configuration.yaml` (create the file if needed). Put quotes around it if it has special characters:

   ```yaml
   veolia_password: "your password"
   ```

2. **Add the sensor platform to `configuration.yaml`.** If you already have a `sensor:` section, add the item to it.

   ```yaml
   sensor:
     - platform: veoliaidf
       username: you@example.com
       password: !secret veolia_password
       scan_interval: 08:00:00
   ```

3. **Check the configuration**: Developer tools, YAML, **Check configuration**. Fix what it reports.
4. **Restart Home Assistant.** A restart is needed the first time, and each time you change this configuration.

| Option | Required | Default | |
|---|---|---|---|
| `platform` | yes | | Always `veoliaidf`. |
| `username` | yes | | Your Veolia login (your email). |
| `password` | yes | | Your Veolia password. Use `!secret`. |
| `scan_interval` | no | `04:00:00` | How often the data is read: `HH:MM:SS`, or `hours: 8`. Veolia publishes the consumption once a day, so a few hours is plenty. Do not go below an hour: you would only load the Veolia site for nothing. |

**Several accounts:** add one item per account, each with its own `username` and `password`. **Several contracts or meters on one account:** the integration reads the first contract and its first meter.

## First start
* About **5 seconds after Home Assistant has started**, the integration logs in to Veolia and reads the last 10 days. The sensors show `unknown` until then.
* After that it updates every `scan_interval`.
* Find the sensors in **Settings, Devices & services, Entities** (search `veolia`), or in Developer tools, States. They have a unique ID, so you can rename them, and change their icon and area, from their settings.
* If a sensor stays `unknown`, see [Troubleshooting](#troubleshooting).

## Entities

| Entity | Unit | Device class | What it is |
|---|---|---|---|
| `sensor.veolia_yesterday_liter` | L | | The consumption of the latest day that Veolia has published (yesterday, usually). |
| `sensor.veolia_total_liter` | L | `water`, state class `total_increasing` | The index of the meter. It only increases, so Home Assistant records long-term statistics for it, and it can be used in the Energy dashboard. When the meter is replaced, the index starts again from a low value, and Home Assistant treats it as a new cycle. |
| `sensor.veolia_period_start_time` | | | The date and time of the reading before the latest one. |
| `sensor.veolia_period_end_time` | | | The date and time of the latest reading. |

Every sensor has these attributes:

| Attribute | Meaning |
|---|---|
| `type` | `Mesuré` (measured) or `Estimé` (estimated): Veolia estimates a day when the meter did not report, and corrects it later. |
| `timestamp` | When the integration last read the data from Veolia. |
| `attribution` | `Data provided by VeoliaIDF`. |

About the times: the date is the day that the Veolia website shows. The hour comes from Veolia (it is usually 21:00, but not always) and is not a clock time that you can rely on, so use the date.

## Energy dashboard
1. Open **Settings, Dashboards, Energy**.
2. Under **Water consumption**, click **Add water source**.
3. Select **`sensor.veolia_total_liter`** and save.

Home Assistant records statistics from the moment it starts reading the sensor: past readings are not imported, and the first value is only a starting point.

## Examples
These are starting points: adapt the names and the values.

**A dashboard card** with the latest values:

```yaml
type: entities
title: Water
entities:
  - entity: sensor.veolia_yesterday_liter
    name: Yesterday
  - entity: sensor.veolia_total_liter
    name: Meter
  - entity: sensor.veolia_period_end_time
    name: Last reading
```

**Consumption per day over a month**, from the statistics of the meter:

```yaml
type: statistics-graph
title: Water per day
chart_type: bar
period: day
days_to_show: 30
stat_types:
  - change
entities:
  - sensor.veolia_total_liter
```

**A notification when yesterday's consumption was high** (a possible leak, a tap left open):

```yaml
automation:
  - alias: "Water: high consumption yesterday"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.veolia_yesterday_liter
        above: 1000
    actions:
      - action: notify.notify
        data:
          title: Water
          message: "Yesterday: {{ states('sensor.veolia_yesterday_liter') }} L"
```

**The meter in cubic meters**, with a template sensor:

```yaml
template:
  - sensor:
      - name: "Water meter m3"
        unit_of_measurement: "m³"
        device_class: water
        state_class: total_increasing
        state: "{{ (states('sensor.veolia_total_liter') | float(0) / 1000) | round(3) }}"
        availability: "{{ has_value('sensor.veolia_total_liter') }}"
```

## Upgrading from a version that needed Firefox
The previous versions (0.4.x) drove Firefox with Selenium. This one does not.

1. Update the integration (HACS, or copy the new `custom_components/veoliaidf` over the old one).
2. **Remove the options** `webdriver`, `firefox_binary_location`, `wait_time` and `tmpdir` from your configuration. If you leave them, Home Assistant logs an error for each one ("has been removed, please remove it") at the start, but the integration works.
3. Delete the `drivers` folder that you may have copied into your configuration, and uninstall Firefox and geckodriver if you installed them only for this integration.
4. Restart Home Assistant.

The entities keep their names and their unique IDs, so their history, your dashboards and your statistics are kept.

## Troubleshooting
First look at the log: **Settings, System, Logs**, and search for `veoliaidf`. To see more, [turn on the debug log](#what-to-include).

| Symptom | Cause and fix |
|---|---|
| `Platform error 'sensor' from integration 'veoliaidf' - Integration 'veoliaidf' not found` | The folder is not where Home Assistant looks. It must be `config/custom_components/veoliaidf/` and hold `manifest.json`. Restart after copying it. |
| `Invalid config for 'veoliaidf' from integration 'sensor' ... required key 'username' not provided` | `username` or `password` is missing, or the item is mis-indented. Use Check configuration. |
| `Requirements for veoliaidf not found: ['pyveoliaidf==...']` | Home Assistant could not install the library: it has no access to PyPI, or the version in `manifest.json` does not exist. Look at the log above that line for the pip error, and check your network. |
| The sensors stay `unknown` | The first update runs 5 seconds after the start: wait a minute. If they stay unknown, the log has the reason: usually the login (below) or the network. |
| `LoginError` in the log | Veolia refused the login or the password. Try them on https://connexion.leaudiledefrance.fr. A password with special characters needs quotes in `secrets.yaml`. If they work on the website, the login page may have changed: see [Reporting an issue](#reporting-an-issue). |
| `UnexpectedResponseError` in the log | The Veolia site has changed. The message names the fields: please report it. |
| The values do not change for a day | Veolia publishes the consumption of a day during the following day. The latest reading is yesterday's, and a day can be an estimate (attribute `type`) until Veolia corrects it. |
| `sensor.veolia_yesterday_liter` looks too low or too high | Check the `type` attribute: `Estimé` means estimated. Compare with the Veolia website. |
| Errors about `webdriver`, `firefox_binary_location`, `wait_time` or `tmpdir` | Leftovers of the old configuration: remove them. |
| `We found a custom integration veoliaidf which has not been tested by Home Assistant` | Normal for every custom integration. |

## Limitations
* The integration reads the **first contract and the first meter** of the account.
* The data is **daily**, and published with a delay of a day: it is not a real-time flow.
* There are four sensors. The cost, the weekly and monthly consumption, and the leak alert of the Veolia website are in the library, but not in sensors yet.
* It is configured in YAML only.
* It depends on how the Veolia customer area is built: if Veolia changes it, the integration may stop working until the library is updated.

# Reporting an issue
Something does not work? Please open an issue at https://github.com/ssenart/home-assistant-veoliaidf/issues. If the cause is in the Veolia data itself (a login error, a missing reading, an `UnexpectedResponseError`), it will be moved to the [pyveoliaidf library](https://github.com/ssenart/pyveoliaidf#reporting-an-issue), which explains in detail how to report.

## First, check these
1. **Does the website work?** Log in at https://connexion.leaudiledefrance.fr and open your consumption history. If it fails there too, it is not the component.
2. **Are you up to date?** Update the component (HACS or a new copy of `custom_components/veoliaidf`) and restart Home Assistant. The site changes, and the fix may be released already: see the [changelog](CHANGELOG.md).
3. **Did you migrate?** The options `webdriver`, `firefox_binary_location`, `wait_time` and `tmpdir` are no longer used. Home Assistant logs an error for each one that is still in your configuration ("has been removed, please remove it"), but the integration works: remove them. See [Upgrading](#upgrading-from-a-version-that-needed-firefox).

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

## Prerequisites
* [git](https://git-scm.com/) and [uv](https://docs.astral.sh/uv/getting-started/installation/). uv downloads the Python version that the project asks for (3.14.2 or newer, the version Home Assistant requires).
* A Veolia account, only for the live test and for trying the integration against the real site.

## Checkout and set up

```bash
git clone https://github.com/ssenart/home-assistant-veoliaidf.git
cd home-assistant-veoliaidf
git switch develop              # the integration branch; see "Creating a release"
uv sync                         # creates .venv with Home Assistant, the library and the test tools, from uv.lock
```

Prefix a command with `uv run` to run it in that environment, or activate it (`source .venv/bin/activate`).

## Project layout

```
custom_components/veoliaidf/
  manifest.json      the metadata of the integration: its version, and the pinned library (requirements)
  __init__.py        empty: the integration only provides a sensor platform
  sensor.py          the platform: the configuration, the account that reads the data, the four sensors
tests/
  test_veoliaidf_offline.py   offline tests: the library is replaced by a fake
  test_veoliaidf_sensor.py    the live test (marked "live")
hacs.json                     HACS metadata
pyproject.toml, uv.lock       the development environment (the integration itself is not a Python package)
.github/workflows/            ci.yaml, create-release.yaml, hassfest-action.yml, hacs-action.yml
```

## How it works
1. Home Assistant calls `async_setup_platform` (`sensor.py`) with the validated configuration (`PLATFORM_SCHEMA`: the username, the password and the scan interval; the removed options are dropped, with an error message).
2. It creates a `VeoliaIDFAccount` with four sensors, schedules the first update 5 seconds later (`INITIAL_UPDATE_DELAY`), and then one every `scan_interval`.
3. An update opens a `pyveoliaidf.Client` as an async context manager, reads the last 10 days (`LAST_N_DAYS`), and converts the readings to rows (`to_rows`: liters as integers, the time as text, the type).
4. The sensors read the last row (or the one before the last) when Home Assistant asks them to update. Their unique ID is built from the login, the row key and the position.

The library does the work with Veolia (the login, the daily range limit, the contracts): see its [documentation](https://github.com/ssenart/pyveoliaidf). The integration creates no HTTP session of its own: the library makes its own, because Home Assistant's shared session keeps no cookies and does not trust the intermediate certificate of the Veolia site.

## The daily workflow

| Task | Command |
|---|---|
| Install or update the environment | `uv sync` |
| Offline tests | `uv run pytest` |
| One test | `uv run pytest tests/test_veoliaidf_offline.py -k unique_ids` |
| Lint | `uv run flake8 custom_components tests` |
| **What CI checks** | `uv run flake8 custom_components tests && uv run pytest` |
| The live test (needs credentials) | `uv run --env-file .env pytest -m live` |
| Run a real Home Assistant with the integration | see below |
| Update the locked dependencies | `uv lock --upgrade && uv sync` |

Run "what CI checks" before you push.

## Tests
* **Offline (default).** `tests/test_veoliaidf_offline.py` replaces `pyveoliaidf.Client` with a fake that returns a known history: no network and no Veolia account. They check the configuration (the options, and the removed ones), what the client is built with and that it is closed, the conversion to rows, the values and the attributes of the sensors, the unique IDs, and the device class and state class of the water meter.
* **Live.** `tests/test_veoliaidf_sensor.py::test_live` is marked `live` and deselected by default. It logs in to Veolia, so put `VEOLIAIDF_USERNAME` and `VEOLIAIDF_PASSWORD` in a `.env` file (git ignores it), then run it. It checks that the four sensors get a state and a timestamp from the real site.
* The library has its own, much larger test suites: do not repeat them here.

## Run a real Home Assistant with the integration
This is the closest check to a user's installation, and it needs no container: Home Assistant is part of the development environment.

```bash
mkdir -p config
ln -s "$PWD/custom_components" config/custom_components      # the sources, not a copy
printf 'veolia_password: "your password"\n' > config/secrets.yaml
```

Put this in `config/configuration.yaml`:

```yaml
homeassistant:
  name: Test
  unit_system: metric
  time_zone: Europe/Paris
logger:
  default: warning
  logs:
    custom_components.veoliaidf: debug
    pyveoliaidf: debug
sensor:
  - platform: veoliaidf
    username: you@example.com
    password: !secret veolia_password
```

Then start it:

```bash
uv run hass -c config
```

In the log, look for `Logged in.` and `New data have been retrieved successfully`, and for warnings such as `Detected blocking call`: Home Assistant reports an integration that blocks its event loop. Open http://localhost:8123, create the local user once, and see the sensors in Developer tools, States. Stop it with Ctrl+C. The `config` folder is ignored by git; its secrets and its debug log hold your login, so do not share them.

## Changing the library
The integration pins the library exactly, in two places that must match: `requirements` in `custom_components/veoliaidf/manifest.json` (what Home Assistant installs) and the dev dependency in `pyproject.toml` (what the tests use). To move to a new version:

1. Change both, run `uv lock`, and run the tests, including the live test.
2. Check the changelog of the library for breaking changes: `to_rows` is the only place that reads its model (`Reading` and `ConsumptionHistory`).

To try an unreleased library, install a local checkout in the environment without committing anything: `uv pip install -e ../pyveoliaidf`. Two things to know:
* **The checkout must report the version that `manifest.json` requires** (its `pyproject.toml` version). Otherwise Home Assistant, which installs the requirement of the manifest when it starts, replaces your checkout with the version from PyPI, and you test the wrong code. Check with `uv run python -c "import pyveoliaidf; print(pyveoliaidf.__file__)"` after a run.
* `uv sync` (and `uv run`) restores the pinned version.

## Adding a sensor
1. Read what the library offers (`ConsumptionHistory` and `Reading`: the cost, the estimated flag, the leak data...).
2. Add the value to the rows in `to_rows`, with a `ROW_...` key, and a name constant `HA_...`.
3. Create the sensor in `VeoliaIDFAccount.__init__`, from `VeoliaIDFSensor` for a plain value or `VeoliaIDFWaterSensor` for a water meter. Give it a unit, and a device class and a state class if Home Assistant has one that fits, so that it works in the dashboards and the statistics.
4. Test it in `tests/test_veoliaidf_offline.py` with the fake history, and try it in a real Home Assistant (above).
5. Document it in the README (the entities table) and the changelog.

## Conventions
* The code is checked with **flake8** (`.flake8`: the line length is not limited). Keep the style of the code around yours.
* **Never log a password or a token.** The debug log of the integration does show the login (`username=...`) and the readings: keep that in mind when you add a log line, and update the issue instructions above if you add more.
* Every change adds a line to `CHANGELOG.md` under `[Unreleased]`, and updates this README if it changes what users see.
* In `sensor.py`, Home Assistant must be imported before voluptuous (its import replaces voluptuous): do not reorder those imports.

## Continuous integration
`.github/workflows/ci.yaml` runs on every push to `main`, `develop`, `release/*` and `feature/*`, on pull requests, and by hand. It lints with flake8 (the settings are in `.flake8`) and runs the offline tests on Python 3.14, the version Home Assistant requires. The live test is not run in CI: the [pyveoliaidf library](https://github.com/ssenart/pyveoliaidf) already tests the site live. `hassfest-action.yml` validates the integration with Home Assistant's own checks.

`hacs-action.yml` runs the HACS validation of the repository (a pinned `hacs/action`, ignoring the brands, requirements and archived checks: the repository ships no brand icon, and the action reads `ignore` as a space-separated list). HACS requires a description and topics on the GitHub repository: they are set.

## Creating a release
The integration is installed from its GitHub release (HACS), so a release publishes nothing outside GitHub. It is created by the **Create Release** workflow (`.github/workflows/create-release.yaml`), run by hand from GitHub: Actions, Create Release, Run workflow.

| Branch | Versions that can be released from it |
|---|---|
| `develop` | Alpha: `X.Y.ZaN` |
| `release/X.Y.Z` | Beta `X.Y.ZbN` or release candidate `X.Y.ZrcN`, with the same `X.Y.Z` as the branch |
| `main` | Final: `X.Y.Z` |

1. Put the changes under `## [Unreleased]` in `CHANGELOG.md`: the workflow refuses an empty section.
2. If the integration needs a new version of the library, change the pin in `custom_components/veoliaidf/manifest.json` and in `pyproject.toml`, run `uv lock`, and merge it first.
3. Check that CI is green on the last commit. The workflow checks it too, and waits for a running CI for up to 30 minutes.
4. Run the workflow with the version (PEP 440, for instance `0.5.0a1`). Keep **draft** ticked, and try it first with **Dry run**: it validates, bumps and reports, and pushes and releases nothing.
5. The workflow bumps the version in `manifest.json`, `pyproject.toml` and `uv.lock`, turns `[Unreleased]` into the version with its date and compare links, commits `Bump version to X.Y.Z`, tags it, and creates the GitHub release (a draft, with the changelog section as notes, marked as a pre-release for an alpha, a beta or a candidate). Publish the draft after checking it.
6. After a final release from `main`, merge `main` back into `develop`.

The version of the component (`manifest.json`) is its own: it does not have to follow the library's.
