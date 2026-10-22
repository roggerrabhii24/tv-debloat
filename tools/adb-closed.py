#!/usr/bin/env python3
"""
adb-closed.py — Verify that port 5555 is closed on the TV after cleanup.

Usage:
    python3 tools/adb-closed.py <tv-ip>

Exits 0 if "Connection refused" (port closed, good).
Exits 1 if connected (port still open, bad).
Exits 2 if "No route to host" — inconclusive on macOS (Local Network privacy).
"""
import socket
import sys

if len(sys.argv) < 2:
    print("Usage: adb-closed.py <tv-ip>")
    sys.exit(3)

ip = sys.argv[1]
port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555

try:
    s = socket.create_connection((ip, port), timeout=5)
    s.close()
    print(f"[OPEN] {ip}:{port} is reachable — ADB is still exposed! ❌")
    sys.exit(1)
except ConnectionRefusedError:
    print(f"[CLOSED] {ip}:{port} refused — ADB is closed. ✅")
    sys.exit(0)
except OSError as e:
    print(f"[INCONCLUSIVE] {ip}:{port} — {e}")
    print("On macOS, 'No route to host' may be Local Network privacy, not a closed port.")
    print("Only 'Connection refused' is proof the port is closed.")
    sys.exit(2)
