# Changelog

## v1.2.2 - 2026-05-18

- Fixed software updater to use the real GitHub Releases API URL for this repository.
- Replaced dynamic `requests` import logic with direct import to avoid packaged Windows false-offline behavior.
- Improved updater diagnostics for connection failure, invalid URL configuration, rate limiting, API failures, and missing platform assets.
- Updated Windows PyInstaller build command with explicit hidden imports for requests dependencies.
- Simplified and modernized header layout: larger logo, title + version only; data/cache metadata moved out of header prominence.
- Noted important release behavior: v1.2.1 must be manually upgraded once to v1.2.2, after which automatic detection of future versions works.

## v1.2.1 - 2026-05-18

- Updated dashboard layout to grouped category cards: Times, Dates, Contact, and General.
- Preserved existing data model and filtering/loading behavior while changing card presentation.
- Fixed read-only text background styling so labels and display text inherit transparent card backgrounds.
- Bumped app and installer version references to 1.2.1 to prepare the official v1.2 release tag.
