# School Information Dashboard

A branded, offline-first cross-platform desktop dashboard for retrieving school information from an Excel data file.

The app is intended for non-technical Windows and macOS users. A user selects a school from a dropdown box, and the dashboard displays stored information such as opening times, term dates, contact details, notes, and other fields from the Excel document.

The application must work offline using a local cached copy of the data. When internet is available, it can check GitHub for updated school data and refresh the local cache.

---

## Project Goal

Build a complete cross-platform desktop application with:

1. A Windows `.exe` build.
2. A proper Windows installer.
3. A macOS `.app` build.
4. A macOS distributable `.dmg` installer/package.

The application should:

- Open as a normal desktop program on Windows and macOS.
- Install through a standard Windows installer and macOS DMG where possible.
- Create Start Menu and optional Desktop shortcuts on Windows.
- Create a normal `.app` bundle on macOS.
- Use a branded GUI with company logo and colours.
- Load school data from an Excel file.
- Let the user select a school from a dropdown.
- Display all available data for that school.
- Work offline using cached data.
- Check GitHub for updated data when internet is available.
- Cache updated data locally.
- Avoid crashing if GitHub is unavailable, the internet is offline, or the Excel file is missing/invalid.

Reliability is more important than fancy features.

---

## Recommended Tech Stack

Use:

- Python 3.11+
- PySide6 for the cross-platform GUI
- pandas for data handling
- openpyxl for reading Excel files
- requests for GitHub data sync
- PyInstaller for building Windows and macOS app bundles
- Inno Setup for creating a Windows installer
- create-dmg or dmgbuild for creating a macOS DMG

Important: Windows and macOS builds must be created on their respective platforms unless CI is configured with suitable runners. Do not assume a Windows machine can produce a fully working signed macOS app.

---

## Expected Project Structure

```text
school_dashboard/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ ui.py
│  ├─ data_loader.py
│  ├─ sync.py
│  ├─ config.py
│  └─ utils.py
├─ assets/
│  ├─ logo.png
│  ├─ app_icon.ico
│  ├─ app_icon.icns
│  └─ theme.json
├─ data/
│  ├─ schools.xlsx
│  └─ version.json
├─ docs/
│  └─ EXCEL_FORMAT.md
├─ installer/
│  ├─ school_dashboard.iss
│  └─ macos_dmg_config.json
├─ tests/
│  └─ test_data_loader.py
├─ requirements.txt
├─ build_exe.bat
├─ build_installer.bat
├─ build_macos_app.sh
├─ build_macos_dmg.sh
├─ .gitignore
└─ README.md
```

---

## Excel Data Format

The Excel file must be named:

```text
schools.xlsx
```

The workbook must contain one sheet named:

```text
schools
```

### Required Columns

| Column | Purpose |
|---|---|
| `school_id` | Unique internal ID for the school |
| `school_name` | Display name shown in the dropdown |

### Recommended Columns

| Column | Purpose |
|---|---|
| `address` | School address |
| `phone` | Main school phone number |
| `email` | Main contact email |
| `website` | School website URL |
| `opening_times` | General opening hours |
| `term_dates` | Current term date information |
| `inset_days` | INSET days |
| `breakfast_club` | Breakfast club details |
| `after_school_club` | After-school club details |
| `notes` | Additional notes |

### Excel Rules

- One row per school.
- No merged cells.
- No blank column headers.
- Extra columns are allowed.
- The app must display extra columns dynamically.
- Blank cells must display as `Not provided`.
- Dates can be stored as plain text for v1.
- Do not store confidential or safeguarding information in GitHub.

---

## Offline-First Behaviour

The app must always use local cached data first.

Windows cache location:

```text
C:\Users\<user>\AppData\Local\SchoolInfoDashboard\data\
```

macOS cache location:

```text
~/Library/Application Support/SchoolInfoDashboard/data/
```

Startup flow:

1. Load cached local Excel data.
2. If cache is missing, copy bundled fallback data.
3. Display dashboard immediately.
4. Optionally check GitHub for updated data.
5. If GitHub is unavailable, continue using cached data.

The app must never require internet access to open.

---

## GitHub Data Sync

Remote files:

```text
data/schools.xlsx
data/version.json
```

Example version.json:

```json
{
  "data_version": "2026-05-18-001",
  "updated_at": "2026-05-18",
  "excel_file": "schools.xlsx",
  "notes": "Initial school data"
}
```

Sync behaviour:

- Compare remote and local `data_version`.
- Download new Excel data when versions differ.
- Validate before replacing cached data.
- Continue using cached data if download fails.
- Include `Check for updates` and `Reload data` buttons.

---

## Branding

Branding files:

```text
assets/logo.png
assets/app_icon.ico
assets/app_icon.icns
assets/theme.json
```

Example theme.json:

```json
{
  "company_name": "Your Company Name",
  "app_title": "School Information Dashboard",
  "primary_colour": "#123456",
  "secondary_colour": "#F5F7FA",
  "accent_colour": "#2D7DD2",
  "text_colour": "#1F2937"
}
```

Branding behaviour:

- Display logo in the top header.
- Use `.ico` as the Windows executable icon.
- Use `.icns` as the macOS app icon.
- Use theme colours throughout the UI.
- Fall back safely if branding assets are missing.

---

## GUI Requirements

The GUI should be simple, clean, and office-friendly.

Required elements:

- Branded top header.
- Company logo or company name.
- App title.
- Data version.
- Offline/cache status.
- Search box.
- School dropdown selector.
- `Check for updates` button.
- `Reload data` button.
- Dynamic school information display.
- Friendly error/status banner.

Data display rules:

- Read all Excel columns dynamically.
- Hide `school_id` from the display.
- Use `school_name` as the selected school title.
- Convert column names into readable labels.
- Long text must wrap neatly.
- Blank values must display as `Not provided`.
- Email and website values should be clickable.

---

## Windows Build Requirements

Include:

```text
build_exe.bat
```

The build script should:

1. Install dependencies.
2. Run PyInstaller.
3. Build a windowed application.
4. Include assets and data files.
5. Output the executable into `/dist`.

Expected output:

```text
dist/SchoolInformationDashboard.exe
```

---

## Windows Installer Requirements

The project must produce a proper Windows installer.

Recommended installer tool:

```text
Inno Setup
```

Include:

```text
installer/school_dashboard.iss
build_installer.bat
```

Expected installer output:

```text
installer_output/SchoolInformationDashboardSetup.exe
```

The installer should:

- Install the app into Program Files by default.
- Use the branded app icon.
- Create a Start Menu shortcut.
- Offer an optional Desktop shortcut.
- Include the built application files from `/dist`.
- Include bundled fallback data and branding assets.
- Preserve user cached data in AppData during upgrades.
- Provide an uninstall entry in Windows Apps/Programs.
- Use a clear app name: `School Information Dashboard`.

---

## macOS Build Requirements

The project must also support a macOS build.

Include:

```text
build_macos_app.sh
```

The macOS build script should:

1. Install dependencies.
2. Run PyInstaller on macOS.
3. Build a windowed `.app` bundle.
4. Use `assets/app_icon.icns` as the macOS app icon.
5. Include bundled `assets` and `data` folders.
6. Output the app bundle into `/dist`.

Expected macOS app output:

```text
dist/School Information Dashboard.app
```

macOS cache must live outside the app bundle:

```text
~/Library/Application Support/SchoolInfoDashboard/data/
```

Do not write cache files inside the `.app` bundle.

---

## macOS DMG Requirements

The project should support creating a distributable macOS DMG.

Include:

```text
build_macos_dmg.sh
installer/macos_dmg_config.json
```

Expected DMG output:

```text
installer_output/SchoolInformationDashboard-macOS.dmg
```

The DMG should:

- Contain the `.app` bundle.
- Include a shortcut/link to the Applications folder where practical.
- Use the branded app icon.
- Preserve user cached data during upgrades because cache is stored in Application Support.

Notes:

- macOS Gatekeeper may warn about unsigned apps.
- Code signing and notarisation are not required for v1 unless explicitly requested later.
- Document unsigned-app opening instructions in the README.

---

## Acceptance Criteria

The build is complete when:

- The app launches from Python.
- The app can be packaged as a Windows `.exe`.
- A Windows installer can be built.
- The installed Windows app launches from the Start Menu.
- The app can be packaged as a macOS `.app` on macOS.
- A macOS DMG can be built on macOS.
- Sample school data loads successfully.
- The dropdown populates from Excel.
- Selecting a school updates the dashboard.
- Blank data displays correctly.
- Branding support works on both platforms.
- Offline cached mode works on both platforms.
- GitHub sync fails safely.
- The app is suitable for non-technical users.

---

## Notes for Codex

- Do not over-engineer the app.
- Do not add databases for v1.
- Do not require user login.
- Build the app cross-platform from the start.
- Include Windows and macOS build paths.
- Keep platform-specific logic isolated in utility/config functions.
- Prioritise reliability over visual complexity.
- Keep the code modular and maintainable.
