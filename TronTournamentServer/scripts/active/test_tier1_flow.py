import io
import json
import zipfile

import requests

BASE_URL = "http://127.0.0.1:5000"


def build_bot_zip_python() -> io.BytesIO:
    bot_code = """import json\nimport sys\n\nfor line in sys.stdin:\n    if not line:\n        break\n    print(json.dumps({\"move\": \"UP\"}))\n    sys.stdout.flush()\n"""
    run_sh = "python3 bot.py\n"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bot.py", bot_code)
        zf.writestr("run.sh", run_sh)
    buf.seek(0)
    return buf


def assert_status(resp, expected):
    if resp.status_code != expected:
        raise RuntimeError(f"Expected {expected}, got {resp.status_code}: {resp.text}")


def main() -> None:
    print("--- Tier 1 Submit/Test Flow ---")

    # 1) create room
    r = requests.post(f"{BASE_URL}/api/rooms", json={"game_key": "tron"}, timeout=20)
    assert_status(r, 201)
    room = r.json()
    room_code = room["room_code"]
    print("Room:", room_code)

    # 2) join participant
    r = requests.post(
        f"{BASE_URL}/api/rooms/{room_code}/join",
        json={"display_name": "FlowTester"},
        timeout=20,
    )
    assert_status(r, 200)

    # 3) submit participant bot
    bot_zip = build_bot_zip_python()
    files = {"bot_zip_file": ("bot.zip", bot_zip, "application/zip")}
    data = {"display_name": "FlowTester", "password": "1234"}
    r = requests.post(f"{BASE_URL}/api/rooms/{room_code}/submit", files=files, data=data, timeout=60)
    assert_status(r, 200)
    print("Submit ok")

    # 4) test against tier1 random benchmark
    bot_zip.seek(0)
    files = {"bot_zip_file": ("bot.zip", bot_zip, "application/zip")}
    data = {"tier": "tier1"}
    r = requests.post(f"{BASE_URL}/api/rooms/{room_code}/test", files=files, data=data, timeout=120)
    assert_status(r, 200)
    payload = r.json()

    print("Test ok")
    print("Winner:", payload.get("winner"))
    print("Termination:", payload.get("termination"))
    print("Has replay:", isinstance(payload.get("replay"), dict))
    print("Has raw_output:", isinstance(payload.get("raw_output"), dict))


if __name__ == "__main__":
    main()
