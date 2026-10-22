#!/usr/bin/env python3
"""
relay.py — Bridges sandbox to ADB over TCP.

Usage:
    python3 tools/relay.py <tv-ip> [--port 5555] [--relay-port 15555]

Listens on 127.0.0.1:15555 (default) and forwards raw bytes to <tv-ip>:5555.
Leave this running in a terminal while the AI agent works.
"""
import socket
import threading
import sys
import argparse


def forward(src: socket.socket, dst: socket.socket, label: str):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except Exception:
        pass
    finally:
        try:
            src.shutdown(socket.SHUT_RD)
        except Exception:
            pass
        try:
            dst.shutdown(socket.SHUT_WR)
        except Exception:
            pass


def handle(client: socket.socket, tv_ip: str, tv_port: int):
    try:
        remote = socket.create_connection((tv_ip, tv_port), timeout=10)
    except Exception as e:
        print(f"[relay] cannot reach {tv_ip}:{tv_port}: {e}")
        client.close()
        return
    t1 = threading.Thread(target=forward, args=(client, remote, "c->r"), daemon=True)
    t2 = threading.Thread(target=forward, args=(remote, client, "r->c"), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    client.close()
    remote.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tv_ip")
    ap.add_argument("--port", type=int, default=5555)
    ap.add_argument("--relay-port", type=int, default=15555)
    args = ap.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", args.relay_port))
    srv.listen(16)
    print(f"[relay] listening on 127.0.0.1:{args.relay_port} → {args.tv_ip}:{args.port}")
    print("[relay] leave this running. Ctrl-C to stop.")
    try:
        while True:
            client, addr = srv.accept()
            threading.Thread(
                target=handle, args=(client, args.tv_ip, args.port), daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\n[relay] stopped.")


if __name__ == "__main__":
    main()
