import subprocess
import threading
import time
import json
from pathlib import Path
import requests

# =========================================================
# Configuration
# =========================================================

NGROK_PORT = 5000
INACTIVITY_TIMEOUT = 300  # seconds

STATE_FILE = Path("admin_state.json")

NGROK_PROCESS = None

# =========================================================
# State helpers
# =========================================================

def touch_activity():
    global LAST_ACTIVITY
    LAST_ACTIVITY = time.time()

def load_state() -> dict:
    return json.loads(STATE_FILE.read_text())

def save_state(**updates):
    state = load_state()
    state.update(updates)
    STATE_FILE.write_text(json.dumps(state, indent=2))

# =========================================================
# Ngrok control
# =========================================================

def start_ngrok():
    global NGROK_PROCESS

    if NGROK_PROCESS:
        return

    print("[ADMIN] Starting ngrok…")

    NGROK_PROCESS = subprocess.Popen(
        ["ngrok", "http", str(NGROK_PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    url = None
    for _ in range(20):
        try:
            r = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=1).json()
            for t in r.get("tunnels", []):
                if t.get("proto") == "https":
                    url = t.get("public_url")
                    break
            if url:
                break
        except Exception:
            time.sleep(0.5)

    save_state(
        active=True,
        ngrok_url=url,
        last_activity=time.time()
    )

    threading.Thread(target=watch_inactivity, daemon=True).start()
    print(f"[ADMIN] ngrok live: {url}")

def stop_ngrok():
    global NGROK_PROCESS

    if NGROK_PROCESS:
        NGROK_PROCESS.terminate()
        NGROK_PROCESS = None

    save_state(
        activate=False,
        active=False,
        ngrok_url=None,
        last_activity=None
    )

    print("[ADMIN] ngrok stopped")

# =========================================================
# Inactivity watchdog
# =========================================================

def watch_inactivity():
    while True:
        time.sleep(5)
        state = load_state()

        if not state["active"]:
            return

        if time.time() - state["last_activity"] > INACTIVITY_TIMEOUT:
            print("[ADMIN] Inactivity timeout reached")
            stop_ngrok()
            return

# =========================================================
# Main supervisor loop
# =========================================================

if __name__ == "__main__":
    print("[ADMIN] Admin access supervisor running")

    while True:
        try:
            state = load_state()

            # Bot requested admin panel
            if state["activate"] and not state["active"]:
                start_ngrok()

            time.sleep(2)

        except KeyboardInterrupt:
            print("\n[ADMIN] Shutting down")
            stop_ngrok()
            break
