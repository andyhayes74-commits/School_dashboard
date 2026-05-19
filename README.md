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

macOS app and DMG builds must be produced on macOS. The v1 scripts and GitHub Actions workflow do not perform Apple code signing or notarisation. Unsigned apps may trigger Gatekeeper warnings; production distribution should add proper Apple Developer ID signing and notarisation later.

## Software Updates (v1.2.5+)

The app now supports GitHub Releases-based software update checks for installer-driven upgrades (no silent in-place binary replacement).

Configuration lives in `app/config.py`:

- `APP_VERSION` (current installed app version, set to `1.2.5` for this release)
- `AUTO_CHECK_SOFTWARE_UPDATES = True`
- `GITHUB_RELEASES_API_URL` (GitHub Releases latest API endpoint)

Update flow:

1. On launch, the app checks the latest GitHub Release when auto-check is enabled.
2. If offline or the check fails, the app continues normally using cached school data.
3. If a newer tag version exists, the app downloads the platform installer into the user cache folder:
   - Windows: `SchoolInformationDashboardSetup.exe`
   - macOS: `SchoolInformationDashboard-macOS.dmg`
4. The app enables **Install update**:
   - Windows: launches the downloaded `.exe` installer and closes the app.
   - macOS: opens the downloaded `.dmg` and instructs the user to install manually.

Cached school data remains in the user cache directory and is not deleted during software update actions.

### macOS install steps (DMG)

1. Download `SchoolInformationDashboard-macOS.dmg`.
2. Open the DMG.
3. Drag **School Information Dashboard** into **Applications**.
4. If macOS blocks the app on first launch, right-click the app in Applications and choose **Open**.

> **Important hotfix note:** v1.2.1 has a broken updater configuration (placeholder GitHub Releases URL and packaged import behavior risk). Install v1.2.5 manually once. After v1.2.5 is installed, future releases (for example v1.2.5 and v1.3.0) are detected automatically via GitHub Releases.

## GitHub Actions Release Builds

The repository includes `.github/workflows/build-release.yml` to build release installers without committing generated build outputs. The workflow runs in three ways:

- Automatically when changes are pushed to `main`: reads the repo-root `VERSION` file, creates/updates tag `v<VERSION>`, then creates/updates the GitHub Release from that tag.
- Automatically when a version tag matching `v*` is pushed, for example `v1.2.5`: builds and publishes that tag's release assets.
- Manually from GitHub Actions using `workflow_dispatch`: builds artifacts only by default; only creates/updates a release when `release_version` input is provided.

The workflow builds and uploads these artifacts:

| Platform | Runner | Output artifact |
|---|---|---|
| Windows | `windows-latest` | `installer_output/SchoolInformationDashboardSetup.exe` |
| macOS | `macos-latest` | `installer_output/SchoolInformationDashboard-macOS.dmg` |

For any run that resolves a release tag, GitHub Actions creates or updates the matching GitHub Release and replaces installer assets so reruns do not fail on existing files. If no tag is resolved (manual run without `release_version`), the workflow uploads artifacts only.

Release flow:

- Merge to `main` = official release flow (tag is created/updated from `VERSION`, then release is created/updated from that tag).
- Push a version tag (`v*`) = official release (artifacts + GitHub Release for that tag).
- Manual `workflow_dispatch` without `release_version` = artifacts only (no release).

To publish a tagged release:

```bash
git tag v1.2.5
git push origin v1.2.5
```

Do not commit `dist/`, `build/`, `installer_output/`, `.exe`, `.dmg`, `.app`, or generated `.xlsx` files; they are ignored build/runtime outputs. The macOS app and DMG produced by this workflow are unsigned unless Apple Developer ID signing and notarisation are added later.

## Manual Steps Before Production

- Place final approved World of Swimming logo/icon files locally in `assets/` before production builds.
- Replace placeholder GitHub raw URLs in `app/config.py`.
- Review and update approved non-confidential school data in `data/schools.csv`, then bump `data/version.json`.
- Produce Windows builds on Windows and macOS builds on macOS.
- Upload built `.exe`, installer, and `.dmg` artifacts to GitHub Releases; do not commit them.
- Add code signing/notarisation if required for managed distribution.


### VERSION file

The repository root `VERSION` file must contain the current application version (for example `1.2.5`). Main-branch release automation reads this file and uses it to manage the `v<VERSION>` tag before publishing/updating the GitHub Release.
