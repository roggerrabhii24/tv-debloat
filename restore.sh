#!/usr/bin/env bash
# restore.sh — Re-enables everything suspended during debloat.
# Usage: ./restore.sh <tv-ip>

TV="${1:-}"
if [ -z "$TV" ]; then
  echo "Usage: ./restore.sh <tv-ip>" >&2
  exit 1
fi

ADB="${ADB:-adb}"
S="$ADB -s $TV:5555"

echo "[restore] Connecting to $TV:5555 ..."
$S wait-for-device

echo "[restore] Re-enabling all suspended packages..."

unsuspend() {
  local pkg="$1"
  echo -n "  unsuspend $pkg ... "
  result=$($S shell pm unsuspend --user 0 "$pkg" 2>&1)
  echo "$result"
}

# ─── Batch 1: Telemetry / ACR ────────────────────────────────────────────────
unsuspend tv.anoki.acr.controller
unsuspend com.homwee.aipont

# ─── Batch 2: Manufacturer bloat ─────────────────────────────────────────────
unsuspend com.cltv.fast
unsuspend com.homwee.store
unsuspend android.autoinstalls.config.homwee
unsuspend com.homwee.help
unsuspend com.mstar.android.tv.disclaimercustomization
unsuspend com.mediatek.testpq

# ─── Batch 3: Duplicate cast/share services ───────────────────────────────────
unsuspend com.homwee.multiscreenshare
unsuspend com.homwee.mmp.screenshare
unsuspend com.homwee.howtocast
unsuspend com.homwee.synckey
unsuspend com.ionitech.airscreen
unsuspend com.google.android.apps.mediashell
unsuspend com.google.android.apps.nbu.smartconnect.tv

# ─── Batch 4: Google services ─────────────────────────────────────────────────
unsuspend com.google.android.katniss
unsuspend com.google.android.backdrop

# ─── Batch 5: Streaming apps ─────────────────────────────────────────────────
unsuspend com.jio.media.stb.ondemand
unsuspend com.sonyliv

# ─── Restore original launcher ───────────────────────────────────────────────
echo ""
echo "[restore] Restoring stock launcher as default home..."
$S shell cmd package set-home-activity com.google.android.tvlauncher/.MainActivity
echo ""
echo "[restore] Re-enabling stock launcher..."
$S shell pm enable --user 0 com.google.android.tvlauncher 2>/dev/null || true

echo ""
echo "[restore] Restore complete. Rebooting TV..."
$S reboot
