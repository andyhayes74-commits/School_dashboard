# Branding Asset Placeholders

Binary image/icon files are intentionally **not committed** to this repository.

Before creating production installers, place approved World of Swimming artwork here:

| Required local file | Purpose |
|---|---|
| `assets/logo.png` | Header logo displayed in the app. If missing, the app shows the company name as a text fallback. |
| `assets/app_icon.ico` | Windows executable and installer icon. If missing, Windows builds run without a custom icon. |
| `assets/app_icon.icns` | macOS `.app` icon. If missing, macOS builds run without a custom icon. |

Do not commit these binary assets to the normal repo history. Keep final artwork in a secure design/source asset location or upload build outputs as GitHub Release artifacts.
