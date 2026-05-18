# v1.0.1 Header Transparency Fix

## Problem

The first Windows build showed white rectangular backgrounds behind the World of Swimming logo and header text. The dashboard content works, but the branded header needs polish.

## Required fixes

1. Replace the local build asset `assets/logo.png` with a true transparent PNG.
2. The logo image must contain only the World of Swimming white artwork on transparent pixels.
3. Do not use a blue or white square background inside the PNG.
4. Use the full logo in the app header.
5. Use the simplified icon in `assets/app_icon.ico` and `assets/app_icon.icns`.
6. Ensure the PySide6 header labels have transparent backgrounds.
7. Scale the logo as a wide image, not a square image.

## UI code changes required in `app/ui.py`

The header logo label should use:

```python
logo.setAttribute(Qt.WA_TranslucentBackground, True)
logo.setAutoFillBackground(False)
logo.setObjectName("brandLogo")
logo.setPixmap(pixmap.scaled(150, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
logo.setFixedSize(160, 74)
```

Header labels should use:

```python
company.setAttribute(Qt.WA_TranslucentBackground, True)
title.setAttribute(Qt.WA_TranslucentBackground, True)
widget.setAttribute(Qt.WA_TranslucentBackground, True)
```

The stylesheet should include:

```css
#header QLabel { background: transparent; border: 0; }
#brandLogo { background: transparent; border: 0; }
#company { background: transparent; color: #DCE7FF; }
#title { background: transparent; color: white; }
#meta { background: transparent; color: #EAF0FF; }
```

## Acceptance criteria

- No white rectangles behind logo, company name, title, or metadata.
- Logo sits cleanly on the blue header.
- Header remains readable on Windows and macOS.
- App still builds with GitHub Actions for Windows and macOS.
