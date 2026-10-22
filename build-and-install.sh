#!/usr/bin/env bash
# build-and-install.sh — Install and set the Apple TV style launcher on the TV
set -euo pipefail

TV="${1:-}"
if [ -z "$TV" ]; then
  echo "Usage: ./build-and-install.sh <tv-ip>" >&2
  exit 1
fi

ADB="${ADB:-adb}"
S="$ADB -s $TV:5555"
APK_PATH="$(dirname "$0")/launcher-bin/app-release.apk"

if [ ! -f "$APK_PATH" ]; then
  echo "Error: $APK_PATH not found." >&2
  exit 1
fi

echo "[install] Connecting to $TV:5555..."
$S connect "$TV:5555"

echo "[install] Pushing APK to TV..."
$S push "$APK_PATH" /data/local/tmp/app-release.apk

echo "[install] Installing package..."
$S shell pm install -r /data/local/tmp/app-release.apk
$S shell rm -f /data/local/tmp/app-release.apk

echo "[install] Optimizing compile speed..."
$S shell cmd package compile -m speed -f com.gathin.tvhome

echo "[install] Setting com.gathin.tvhome as default Home..."
$S shell cmd package set-home-activity --user 0 com.gathin.tvhome/.MainActivity

echo "[install] Disabling stock launcher..."
$S shell pm disable-user --user 0 com.google.android.tvlauncher || true

echo "[install] Launching home..."
$S shell am start -W -n com.gathin.tvhome/.MainActivity

echo "[install] Verified default launcher:"
$S shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME
echo "Done!"
