#!/usr/bin/env python3
"""
tv.py — Thin wrapper around adb for this project.

Usage:
    python3 tools/tv.py 'shell command'
    python3 tools/tv.py --screenshot shots/name.png [KEY ...]
    python3 tools/tv.py --install path/to/app.apk

Environment:
    TV_HOST  — IP to connect to (default: 127.0.0.1 when relay is running)
    TV_PORT  — ADB port (default: 15555 when relay, 5555 direct)
    ADB      — Path to adb binary (default: auto-detect)
"""
import os
import sys
import subprocess
import shutil
import time
import argparse

ADB = os.environ.get("ADB") or shutil.which("adb") or "/opt/homebrew/bin/adb"
TV_HOST = os.environ.get("TV_HOST", "127.0.0.1")
TV_PORT = os.environ.get("TV_PORT", "15555")
DEVICE = f"{TV_HOST}:{TV_PORT}"


def run(args, check=True, capture=False):
    full = [ADB, "-s", DEVICE] + args
    if capture:
        r = subprocess.run(full, capture_output=True, text=True)
        return r
    else:
        return subprocess.run(full, check=check)


def screenshot(path: str, keys: list[str]):
    """Optionally inject keys, then pull a screenshot."""
    for key in keys:
        run(["shell", "input", "keyevent", key])
        time.sleep(0.3)
    time.sleep(0.5)
    # Take screenshot on device
    r = run(["shell", "screencap", "-p", "/data/local/tmp/_shot.png"], check=False)
    if r.returncode != 0:
        print("screencap failed — live content (Netflix/HDMI) may block it.", file=sys.stderr)
        sys.exit(1)
    run(["pull", "/data/local/tmp/_shot.png", path])
    run(["shell", "rm", "/data/local/tmp/_shot.png"])
    size = os.path.getsize(path) if os.path.exists(path) else 0
    if size == 0:
        print("Screenshot is 0 bytes — protected content on screen.", file=sys.stderr)
        os.remove(path)
        sys.exit(1)
    print(f"[tv.py] screenshot saved: {path} ({size} bytes)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screenshot", metavar="PATH", help="Save screenshot to PATH")
    ap.add_argument("--install", metavar="APK", help="Install an APK")
    ap.add_argument("remainder", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    if args.screenshot:
        screenshot(args.screenshot, args.remainder)
    elif args.install:
        apk = args.install
        remote = "/data/local/tmp/_install.apk"
        print(f"[tv.py] pushing {apk} → {remote}")
        run(["push", apk, remote])
        print("[tv.py] running pm install -r ...")
        r = run(["shell", "pm", "install", "-r", remote], check=False, capture=True)
        print(r.stdout, r.stderr)
        run(["shell", "rm", remote])
    else:
        # Pass-through shell command
        cmd = " ".join(args.remainder)
        if not cmd:
            ap.print_help()
            sys.exit(1)
        r = run(["shell", cmd], capture=True, check=False)
        if r.stdout:
            print(r.stdout, end="")
        if r.stderr:
            print(r.stderr, end="", file=sys.stderr)
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
