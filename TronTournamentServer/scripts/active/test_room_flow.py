import io
import json
import time
import zipfile

import requests

SERVER_URL = "http://127.0.0.1:5000"


def make_dummy_bot_zip(move="UP"):
    bot_code = f"""
import sys
import json

while True:
    line = sys.stdin.readline()
    if not line:
        break
    print(json.dumps({{"move": "{move}"}}))
    sys.stdout.flush()
"""
    run_script = "python3 bot.py"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bot.py", bot_code)
        zf.writestr("run.sh", run_script)
    buf.seek(0)
    return buf


def post_json(path, payload):
    resp = requests.post(f"{SERVER_URL}{path}", json=payload, timeout=30)
    return resp.status_code, resp.text, resp


def post_submit(room_code, name, password, zipbuf):
    zipbuf.seek(0)
    files = {"bot_zip_file": ("bot.zip", zipbuf, "application/zip")}
    data = {"display_name": name, "password": password}
    resp = requests.post(f"{SERVER_URL}/api/rooms/{room_code}/submit", files=files, data=data, timeout=60)
    return resp.status_code, resp.text, resp


def get_json(path):
    resp = requests.get(f"{SERVER_URL}{path}", timeout=30)
    return resp.status_code, resp.text, resp


def main():
    print("--- Room Flow Smoke Test ---")

    # 1) Create room
    code, text, resp = post_json("/api/rooms", {"game_key": "tron"})
    print("Create room:", code, text)
    if code != 201:
        return
    room = resp.json()
    room_code = room["room_code"]

    # 2) Join two participants
    for name in ["Alice", "Bob"]:
        code, text, _ = post_json(f"/api/rooms/{room_code}/join", {"display_name": name})
        print(f"Join {name}:", code, text)

    # 3) Submit bots
    code, text, _ = post_submit(room_code, "Alice", "alicepw", make_dummy_bot_zip("UP"))
    print("Submit Alice:", code, text)
    code, text, _ = post_submit(room_code, "Bob", "bobpw", make_dummy_bot_zip("LEFT"))
    print("Submit Bob:", code, text)

    # 4) Queue a match
    code, text, _ = post_json(f"/api/rooms/{room_code}/queue-match", {})
    print("Queue match:", code, text)
    if code != 202:
        return

    # 5) Poll recent matches
    print("Polling recent matches (up to 45s)...")
    for _ in range(15):
        time.sleep(3)
        code, text, resp = get_json(f"/api/rooms/{room_code}/matches/recent")
        if code != 200:
            print("Recent matches error:", code, text)
            continue
        matches = resp.json()
        if matches:
            print("Recent matches:", json.dumps(matches[:1], indent=2))
            break
    else:
        print("No room matches observed yet. Check worker/docker logs.")

    # 6) Fetch leaderboard
    code, text, _ = get_json(f"/api/rooms/{room_code}/leaderboard")
    print("Leaderboard:", code, text)


if __name__ == "__main__":
    main()
