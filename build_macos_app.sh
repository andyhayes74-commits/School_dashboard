#!/usr/bin/env bash
set -euo pipefail
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "macOS .app builds must be produced on macOS."
  exit 1
fi
python3 -m pip install -r requirements.txt
python3 -m app.sample_excel
ICON_ARGS=()
if [[ -f assets/app_icon.icns ]]; then
  ICON_ARGS=(--icon assets/app_icon.icns)
else
  echo "assets/app_icon.icns not found; building without a custom macOS icon."
fi
python3 -m PyInstaller --noconfirm --clean --windowed \
  --name "School Information Dashboard" \
  "${ICON_ARGS[@]}" \
  --add-data "assets:assets" \
  --add-data "data:data" \
  app/main.py
echo "Built dist/School Information Dashboard.app"
