#!/usr/bin/env bash
set -euo pipefail
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "macOS DMG builds must be produced on macOS."
  exit 1
fi
APP_PATH="dist/School Information Dashboard.app"
DMG_PATH="installer_output/SchoolInformationDashboard-macOS.dmg"
STAGING_DIR="installer_output/dmg_staging"
if [[ ! -d "$APP_PATH" ]]; then
  ./build_macos_app.sh
fi
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR" installer_output
cp -R "$APP_PATH" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"
rm -f "$DMG_PATH"
if command -v create-dmg >/dev/null 2>&1; then
  create-dmg --volname "School Information Dashboard" --window-pos 200 120 --window-size 640 420 \
    --icon "School Information Dashboard.app" 160 190 --app-drop-link 460 190 \
    "$DMG_PATH" "$STAGING_DIR"
else
  hdiutil create -volname "School Information Dashboard" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_PATH"
fi
rm -rf "$STAGING_DIR"
echo "Built $DMG_PATH"
