# School Information Dashboard

A branded, offline-first desktop dashboard for retrieving school information from cached school data. v1 is built for **World of Swimming** using Python 3.11+, PySide6, pandas/openpyxl, requests, PyInstaller, Inno Setup, and macOS app/DMG build scripts.

## What the App Does

- Opens as a normal desktop app on Windows and macOS.
- Copies bundled fallback data into a writable offline cache on first launch.
- Loads cached `schools.xlsx` immediately; internet is never required to open.
- Lets users search for and select a school from a dropdown.
- Dynamically displays every Excel column except `school_id`.
- Converts labels such as `opening_times` to `Opening Times`.
- Displays blank optional values as `Not provided`.
- Makes email and website values clickable where practical.
- Can manually check GitHub raw URLs for updated CSV school data.
- Validates downloaded CSV data and generated Excel runtime data before replacing the local cache.

## Branding

Branding lives in `assets/`:

| File | Purpose |
|---|---|
| `assets/theme.json` | World of Swimming colours and app title |
| `assets/README.md` | Documents where local logo/icon files should be placed |

Binary logo and icon files are intentionally not committed. Place approved local files at `assets/logo.png`, `assets/app_icon.ico`, and `assets/app_icon.icns` before production builds. If `logo.png` is missing, the app displays a company-name text fallback.

Theme colours:

- Primary: `#23408F`
- Secondary: `#F5F7FA`
- Accent: `#3B82F6`
- Text: `#1F2937`

## Project Structure

```text
app/                         Python application package
assets/                      Branding and icon assets
data/                        Source-controlled CSV school data, version file, and data docs
docs/EXCEL_FORMAT.md         CSV school-data editing guide
installer/                   Windows Inno Setup and macOS DMG config
tests/                       Data loading and sync safety tests
build_exe.bat                Windows PyInstaller build
build_installer.bat          Windows Inno Setup build
build_macos_app.sh           macOS .app build
build_macos_dmg.sh           macOS DMG build
requirements.txt             Runtime/build/test dependencies
```

## School Data

Source-controlled school data lives in `data/schools.csv`. The app keeps a local cached runtime workbook named `schools.xlsx`; `python -m app.sample_excel` can generate a local ignored `data/schools.xlsx` for builds or manual validation when needed. To publish a school-data update, edit `data/schools.csv` and bump `data/version.json`.

Required columns:

- `school_id`
- `school_name`

Recommended columns:

- `address`
- `phone`
- `email`
- `website`
- `opening_times`
- `term_dates`
- `inset_days`
- `breakfast_club`
- `after_school_club`
- `notes`

See [docs/EXCEL_FORMAT.md](docs/EXCEL_FORMAT.md) for the full CSV editing guide and data safety warning. Do not store confidential, safeguarding, pupil-sensitive, or staff-sensitive data in GitHub-hosted files.

## Offline Cache Locations

The app keeps user data outside the installed application so upgrades do not delete cached school data.

| Platform | Cache location |
|---|---|
| Windows | `%LOCALAPPDATA%\SchoolInfoDashboard\data\` |
| macOS | `~/Library/Application Support/SchoolInfoDashboard/data/` |
| Linux/dev fallback | `$XDG_DATA_HOME/SchoolInfoDashboard/data/` or `~/.local/share/SchoolInfoDashboard/data/` |

Startup flow:

1. Resolve the platform-specific cache directory.
2. Create the cache directory if needed.
3. Copy bundled `data/schools.xlsx` into cache if present; otherwise generate cached `schools.xlsx` from committed `data/schools.csv`.
4. Copy bundled `data/version.json` into cache if missing.
5. Load cached Excel data.
6. Display the dashboard immediately.
7. Continue using cached data if remote updates fail.

## GitHub Sync Placeholders

Remote URLs are configured in `app/config.py`:

- `REMOTE_VERSION_URL`
- `REMOTE_DATA_URL`

They currently contain placeholder raw GitHub URLs on the `main` branch. Before real update distribution, replace `OWNER/REPOSITORY` with the approved repository that hosts non-confidential school data.

Sync behaviour:

1. Download remote `version.json`.
2. Compare remote `data_version` with the cached version.
3. Download remote `schools.csv` only when versions differ.
4. Validate the downloaded CSV file.
5. Generate a temporary `schools.xlsx` runtime workbook and validate it.
6. Replace cached files only after validation succeeds.
7. Keep existing cached data if any step fails.

## Run From Source

```bash
python -m pip install -r requirements.txt
python -m app.main
```

## Run Tests

```bash
pytest
```

## Build Windows Executable

Run on Windows:

```bat
build_exe.bat
```

Expected output:

```text
dist\SchoolInformationDashboard.exe
```

## Build Windows Installer

Install Inno Setup first and ensure `ISCC.exe` is on `PATH`, then run on Windows:

```bat
build_installer.bat
```

Expected output:

```text
installer_output\SchoolInformationDashboardSetup.exe
```

The installer installs to Program Files by default, creates a Start Menu shortcut, offers an optional Desktop shortcut, uses the app icon, and leaves `%LOCALAPPDATA%\SchoolInfoDashboard\data\` untouched during upgrades/uninstall.

## Build macOS App

Run on macOS:

```bash
./build_macos_app.sh
```

Expected output:

```text
dist/School Information Dashboard.app
```

## Build macOS DMG

Run on macOS with `create-dmg` installed, or use the built-in `hdiutil` fallback:

```bash
./build_macos_dmg.sh
```

Expected output:

```text
installer_output/SchoolInformationDashboard-macOS.dmg
```

macOS app and DMG builds must be produced on macOS. The v1 scripts do not perform code signing or notarisation. Unsigned apps may trigger Gatekeeper warnings; production distribution should add proper Apple Developer ID signing and notarisation later.

## Manual Steps Before Production

- Place final approved World of Swimming logo/icon files locally in `assets/` before production builds.
- Replace placeholder GitHub raw URLs in `app/config.py`.
- Review and update approved non-confidential school data in `data/schools.csv`, then bump `data/version.json`.
- Produce Windows builds on Windows and macOS builds on macOS.
- Upload built `.exe`, installer, and `.dmg` artifacts to GitHub Releases; do not commit them.
- Add code signing/notarisation if required for managed distribution.
