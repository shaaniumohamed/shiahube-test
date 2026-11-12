"""Starts the dashboard and opens it in your browser.

Normally you do not run this yourself: double-click start.bat (Windows) or
start.command (Mac). Close the black window to stop the app.
"""
from __future__ import annotations

import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def free_port(preferred: int = 8501) -> int:
    for port in range(preferred, preferred + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return preferred


def lan_address() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))          # no data is sent
            return s.getsockname()[0]
    except OSError:
        return None


def open_when_ready(port: int) -> None:
    for _ in range(120):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                webbrowser.open(f"http://localhost:{port}")
                return
        time.sleep(0.5)


def main() -> int:
    port = free_port()
    print()
    print("  Project dashboard is starting...")
    print(f"  On this computer:  http://localhost:{port}")
    address = lan_address()
    if address and not address.startswith("127."):
        print(f"  On your phone (same Wi-Fi):  http://{address}:{port}")
    print("  Keep this window open while you use the dashboard. Close it to stop.")
    print()
    threading.Thread(target=open_when_ready, args=(port,), daemon=True).start()
    command = [sys.executable, "-m", "streamlit", "run", str(ROOT / "app" / "main.py"),
               "--server.port", str(port), "--server.headless", "true",
               "--browser.gatherUsageStats", "false"]
    try:
        return subprocess.call(command, cwd=ROOT)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
