#!/usr/bin/env python3
"""
adb_server.py — Local HTTP bridge: lets the AI agent run ADB commands
through YOUR terminal's already-authenticated ADB session.

Usage (in a second terminal, alongside relay.py):
    python3 tools/adb_server.py

Listens on http://127.0.0.1:15556
Endpoints:
    POST /shell    body = shell command string  → stdout text
    POST /push     body = JSON {"local": "...", "remote": "..."}
    POST /pull     body = JSON {"remote": "...", "local": "..."}
    POST /screenshot  body = JSON {"path": "...", "keys": [...]}
    POST /install  body = JSON {"apk": "..."}
    GET  /ping     → "pong"
"""

import http.server
import json
import os
import subprocess
import sys
import base64
import tempfile
import threading
import time

ADB = os.environ.get("ADB", "/opt/homebrew/bin/adb")
TV = os.environ.get("TV", "127.0.0.1:5555")
PORT = int(os.environ.get("BRIDGE_PORT", "15556"))


def adb(*args, capture=True, timeout=60):
    cmd = [ADB, "-s", TV] + list(args)
    if capture:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    else:
        return subprocess.run(cmd, timeout=timeout).returncode, "", ""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[bridge] {self.address_string()} {fmt % args}")

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length).decode()

    def _respond(self, code: int, body: str):
        enc = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(enc)))
        self.end_headers()
        self.wfile.write(enc)

    def do_GET(self):
        if self.path == "/ping":
            self._respond(200, "pong")
        else:
            self._respond(404, "not found")

    def do_POST(self):
        body = self._read_body()

        if self.path == "/shell":
            cmd = body.strip()
            print(f"[bridge] shell: {cmd}")
            code, out, err = adb("shell", cmd)
            self._respond(200 if code == 0 else 500, out + err)

        elif self.path == "/push":
            data = json.loads(body)
            local, remote = data["local"], data["remote"]
            print(f"[bridge] push: {local} → {remote}")
            # If local is a base64 payload, decode to temp file first
            if "base64" in data:
                raw = base64.b64decode(data["base64"])
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
                tmp.write(raw)
                tmp.close()
                local = tmp.name
            code, out, err = adb("push", local, remote)
            if "base64" in data:
                os.unlink(local)
            self._respond(200 if code == 0 else 500, out + err)

        elif self.path == "/pull":
            data = json.loads(body)
            remote, local = data["remote"], data["local"]
            print(f"[bridge] pull: {remote} → {local}")
            os.makedirs(os.path.dirname(os.path.abspath(local)), exist_ok=True)
            code, out, err = adb("pull", remote, local)
            self._respond(200 if code == 0 else 500, out + err)

        elif self.path == "/screenshot":
            data = json.loads(body) if body.strip() else {}
            path = data.get("path", "/tmp/shot.png")
            keys = data.get("keys", [])
            print(f"[bridge] screenshot → {path}, keys={keys}")
            for k in keys:
                adb("shell", f"input keyevent {k}")
                time.sleep(0.35)
            if keys:
                time.sleep(0.5)
            adb("shell", "screencap -p /data/local/tmp/_shot.png")
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            code, out, err = adb("pull", "/data/local/tmp/_shot.png", path)
            adb("shell", "rm /data/local/tmp/_shot.png")
            size = os.path.getsize(path) if os.path.exists(path) else 0
            if size == 0:
                self._respond(503, "Screenshot 0 bytes — protected content on screen")
                return
            self._respond(200, f"OK {size} bytes → {path}")

        elif self.path == "/install":
            data = json.loads(body)
            apk = data["apk"]
            remote = "/data/local/tmp/_install.apk"
            print(f"[bridge] install: {apk}")
            adb("push", apk, remote)
            code, out, err = adb("shell", f"pm install -r {remote}", timeout=120)
            adb("shell", f"rm {remote}")
            self._respond(200 if code == 0 else 500, out + err)

        else:
            self._respond(404, f"unknown endpoint: {self.path}")


def main():
    print(f"[bridge] ADB bridge listening on http://127.0.0.1:{PORT}")
    print(f"[bridge] Using ADB={ADB}, TV={TV}")
    print(f"[bridge] Press Ctrl-C to stop.\n")
    # Quick sanity check
    code, out, err = adb("shell", "echo bridge_ok")
    if "bridge_ok" not in out:
        print(f"[bridge] WARNING: ADB shell test failed (code={code}): {err.strip()}")
        print("[bridge]   Make sure your ADB session is still connected.")
    else:
        print(f"[bridge] ADB shell test OK ✅")

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[bridge] stopped.")


if __name__ == "__main__":
    main()
