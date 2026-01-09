import subprocess
import threading
import time
import json
from pathlib import Path
import requests

NGROK_PORT = 5000
INACTIVITY_TIMEOUT = 300

STATE_FILE = Path("admin_state.json")
CONFIG_FILE = Path("admin_config.json")

LAST_ACTIVITY = time.time()
NGROK_PROCESS = None


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def write_state(url=None, active=False):
    STATE_FILE.write_text(json.dumps({
        "ngrok_url": url,
        "active": active,
        "last_updated": time.time()
    }, indent=2))


def touch_activity():
    global LAST_ACTIVITY
    LAST_ACTIVITY = time.time()


def ngrok_running() -> bool:
    return NGROK_PROCESS is not None


# ---------------------------------------------------------
# Admin validation (optional reuse)
# ---------------------------------------------------------

def is_admin(user_id: int) -> bool:
    data = json.loads(CONFIG_FILE.read_text())
    return user_id in data.get("admins", [])


# ---------------------------------------------------------
# Ngrok control
# ---------------------------------------------------------

"""
def start_ngrok():
    global NGROK_PROCESS, LAST_ACTIVITY

    LAST_ACTIVITY = time.time()

    NGROK_PROCESS = subprocess.Popen(
        ["ngrok", "http", str(NGROK_PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    url = None
    for _ in range(10):
        try:
            tunnels = requests.get("http://127.0.0.1:4040/api/tunnels").json()
            for t in tunnels["tunnels"]:
                if t["proto"] == "https":
                    url = t["public_url"]
                    break
            if url:
                break
        except Exception:
            time.sleep(0.5)

    write_state(url=url, active=True)

    threading.Thread(target=_watch_inactivity, daemon=True).start()
    print(f"[ADMIN] ngrok started: {url}")
"""

def start_ngrok():
    global NGROK_PROCESS, LAST_ACTIVITY

    if NGROK_PROCESS:
        touch_activity()
        # Read URL from state file
        try:
            state = json.loads(STATE_FILE.read_text())
            return state.get("ngrok_url")
        except Exception:
            return None

    LAST_ACTIVITY = time.time()

    NGROK_PROCESS = subprocess.Popen(
        ["ngrok", "http", str(NGROK_PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    url = None
    for _ in range(20):
        try:
            tunnels = requests.get(
                "http://127.0.0.1:4040/api/tunnels",
                timeout=1
            ).json()

            for t in tunnels.get("tunnels", []):
                if t.get("proto") == "https":
                    url = t.get("public_url")
                    break

            if url:
                break

        except Exception:
            time.sleep(0.5)

    write_state(url=url, active=bool(url))

    threading.Thread(
        target=_watch_inactivity,
        daemon=True
    ).start()

    print(f"[ADMIN] ngrok started: {url}")
    return url


def stop_ngrok():
    global NGROK_PROCESS
    if NGROK_PROCESS:
        NGROK_PROCESS.terminate()
        NGROK_PROCESS = None

    write_state(url=None, active=False)
    print("[ADMIN] ngrok stopped")


# ---------------------------------------------------------
# Inactivity watchdog
# ---------------------------------------------------------

def _watch_inactivity():
    while NGROK_PROCESS:
        time.sleep(5)
        if time.time() - LAST_ACTIVITY > INACTIVITY_TIMEOUT:
            print("[ADMIN] Inactive — shutting down ngrok")
            stop_ngrok()
            break


# ---------------------------------------------------------
# Standalone entrypoint
# ---------------------------------------------------------

"""
if __name__ == "__main__":
    print("[ADMIN] Starting admin access service...")
    start_ngrok()

    while True:
        time.sleep(1)
"""

if __name__ == "__main__":
    print("[ADMIN] Admin access service running")

    while True:
        try:
            # If ngrok is not running, wait for activity trigger
            if not ngrok_running():
                start_ngrok()
                time.sleep(2)
                continue

            # ngrok is running — just idle
            time.sleep(5)

        except KeyboardInterrupt:
            print("\n[ADMIN] Shutting down")
            stop_ngrok()
            break
