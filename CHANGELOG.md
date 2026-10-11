# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0a1] - 2026-10-11

### Changed
- **Breaking for the installation:** the component uses the asynchronous pyveoliaidf 0.5.0, which calls the Veolia backend over HTTPS. Firefox, geckodriver and Selenium are no longer needed, and the update no longer runs in a thread: it awaits the library, with a client that is closed after each update.
- The options `webdriver`, `firefox_binary_location`, `wait_time` and `tmpdir` are no longer used. An existing configuration that has them keeps working: Home Assistant logs an error for each one ("has been removed, please remove it") and ignores them.
- The component builds its own rows from the typed readings of the library (liters as integers), since the library no longer returns dicts.
- The component requires `pyveoliaidf==0.5.0a2`, which builds its TLS context off the event loop: Home Assistant no longer logs "Detected blocking call" warnings. The development environment installs the same pre-release from PyPI.
- The development environment is managed with uv (`pyproject.toml`, `uv.lock`) and needs Python 3.14.2 or newer. The README describes the setup.
- The total liter sensor is a water meter: device class `water`, state class `total_increasing`, unit liters. It can be selected as a water source in the Energy dashboard, and Home Assistant records its long-term statistics.
- Offline tests run by default. The live test is marked `live` and runs with `pytest -m live`.
- The hassfest workflow uses `actions/checkout@v4` and a pinned hassfest action.

### Added
- A complete README for users: installation (HACS and manual), configuration, the entities and their attributes, the Energy dashboard, dashboard, automation and template examples, upgrading from the Firefox version, troubleshooting with the real error messages, and how to report an issue (with a GitHub bug report form). The configuration example of the previous README was mis-indented and invalid YAML.
- A developer section: checkout, layout, how it works, the daily commands, the tests, running a real Home Assistant from the development environment, changing the pinned library, adding a sensor, and the conventions.
- GitHub workflows aligned with the other Home Assistant integrations of the suite: a CI (flake8, offline tests on Python 3.14) and a Create Release workflow that bumps `manifest.json`, `pyproject.toml` and `uv.lock`, finalizes the changelog, tags, and creates the GitHub release. The HACS check is enabled, and the GitHub repository has topics, which HACS requires.

### Fixed
- The timestamp and type attributes are shown again. They were exposed through `device_state_attributes`, which Home Assistant no longer reads; they are now exposed through `extra_state_attributes`.
- The username is no longer exposed as an entity attribute.
- The liter sensors report a number instead of text.
- Each sensor has a `unique_id`, so Home Assistant can manage it in its entity registry.
- Errors are caught as `Exception`, so a shutdown is no longer swallowed by the error handlers.
- The password is documented as a `secrets.yaml` entry (`!secret`).

### Removed
- The bundled `drivers/` folder (geckodriver binaries) and the geckodriver and Firefox installation notes of the README.
- `requirements.txt`, replaced by `pyproject.toml`.
- The unused `pandas` development dependency.

## [0.4.1] - 2025-01-02

### Changed
[#2](https://github.com/ssenart/home-assistant-veoliaidf/issues/2): Upgrade to PyVeoliaIDF version 0.4.1.

## [0.4.0] - 2025-01-02

### Changed
[#1](https://github.com/ssenart/home-assistant-veoliaidf/issues/1): Upgrade to PyVeoliaIDF version 0.4.0.

## [0.2.0] - 2022-10-16

### Changed
- Upgrade to PyVeoliaIDF version 0.2.0.

[Unreleased]: https://github.com/ssenart/home-assistant-veoliaidf/compare/0.5.0a1...HEAD
[0.5.0a1]: https://github.com/ssenart/home-assistant-veoliaidf/compare/0.4.2a1...0.5.0a1
