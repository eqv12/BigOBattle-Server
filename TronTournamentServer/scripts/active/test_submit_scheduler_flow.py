import io
import json
import os
import time
import zipfile

from server.config import DATABASE_FILE


def _reset_database_file():
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
        print(f"Removed existing database: {DATABASE_FILE}")


def _ensure_fresh_database():
    from server.database import db_setup, db_handler

    _reset_database_file()
    db_setup.setup_database()
    db_handler.ensure_room_schema()
    print("Database reset complete.")


def _zip_bot(bot_code, run_sh="python3 bot.py\n"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bot.py", bot_code)
        zf.writestr("run.sh", run_sh)
    buf.seek(0)
    return buf


def _random_bot_code():
    return """import sys
import json
import random

def main(): 
    for line in sys.stdin:
        state = json.loads(line)
        
        width = state["board"]["width"]
        height = state["board"]["height"]
        grid = state["board"]["grid"]
        head = state["you"]["head"]
        
        possible_moves = ["UP", "DOWN", "LEFT", "RIGHT"]
        safe_moves = []

        # Check each possible move
        for move in possible_moves:
            hx, hy = head["x"], head["y"]
            if move == "UP": hy -= 1
            if move == "DOWN": hy += 1
            if move == "LEFT": hx -= 1
            if move == "RIGHT": hx += 1
            
            # Check for wall collisions
            if not (0 <= hx < width and 0 <= hy < height):
                continue
            
            # Check for body collisions (self or opponent)
            if grid[hy][hx] != '0':
                continue
            
            safe_moves.append(move)

        # Choose a move
        if safe_moves:
            chosen_move = random.choice(safe_moves)
        else:
            # If no move is safe, just move anywhere and accept fate
            chosen_move = random.choice(possible_moves)

        # Send the move back to the game engine
        response = {"move": chosen_move}
        print(json.dumps(response))
        sys.stdout.flush()

if __name__ == "__main__":
    main()
"""


def _greedy_bot_code():
    return """import sys
import json

def main():
    # This bot has a preferred order of moves. It will try them sequentially.
    move_order = ["UP", "RIGHT", "DOWN", "LEFT"]

    for line in sys.stdin:
        # Parse the incoming JSON state
        state = json.loads(line)
        
        board = state["board"]
        width = board["width"]
        height = board["height"]
        grid = board["grid"]

        head = state["you"]["head"]
        hx = head["x"]
        hy = head["y"]
        
        chosen_move = None

        # Check each preferred move in order
        for move in move_order:
            next_x, next_y = hx, hy
            
            if move == "UP":
                next_y -= 1
            elif move == "DOWN":
                next_y += 1
            elif move == "LEFT":
                next_x -= 1
            elif move == "RIGHT":
                next_x += 1

            # Check if the move is safe (within bounds and the cell is '0' / empty)
            if 0 <= next_x < width and 0 <= next_y < height:
                if grid[next_y][next_x] == '0':
                    chosen_move = move
                    break  # Found a safe move, stop searching

        # If no moves are safe, just pick the first preference and accept fate
        if chosen_move is None:
            chosen_move = move_order[0]
            
        # Send back the response
        response = {"move": chosen_move}
        print(json.dumps(response))
        sys.stdout.flush()

if __name__ == "__main__":
    main()
"""


def _space_filler_bot_code():
    return """import sys
import json
import random
from collections import deque

# A value of 1.0 means the bot is completely deterministic (always picks the best).
# A value of 0.0 means it's a random non-suicidal bot.
# 0.8 means it will randomly choose from any move that leads to an area
# at least 80% as large as the best possible area.
RANDOMNESS_FACTOR = 0.8

def flood_fill(start_node, width, height, grid_str):
    q = deque([start_node])
    visited = {start_node}
    count = 0
    while q:
        x, y = q.popleft()
        count += 1
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited and grid_str[ny][nx] == '0':
                visited.add((nx, ny))
                q.append((nx, ny))
    return count

def main():
    for line in sys.stdin:
        state = json.loads(line)
        
        board = state["board"]
        width, height, grid = board["width"], board["height"], board["grid"]
        head = state["you"]["head"]
        hx, hy = head["x"], head["y"]
        
        moves = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
        safe_moves = {}

        # First, find all safe moves and calculate the area they lead to
        for move, (dx, dy) in moves.items():
            nx, ny = hx + dx, hy + dy
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == '0':
                area_size = flood_fill((nx, ny), width, height, grid)
                safe_moves[move] = area_size
        
        # Now, decide which move to make
        if safe_moves:
            # Find the size of the best possible area
            max_area = max(safe_moves.values())
            
            # Create a list of all moves that are "good enough" based on the randomness factor
            good_enough_moves = []
            for move, area in safe_moves.items():
                if area >= max_area * RANDOMNESS_FACTOR:
                    good_enough_moves.append(move)
            
            # Choose randomly from the list of good moves
            best_move = random.choice(good_enough_moves)
        else:
            best_move = "UP" # If trapped, just default to UP and accept fate

        response = {"move": best_move}
        print(json.dumps(response))
        sys.stdout.flush()

if __name__ == "__main__":
    main()
"""


def _post_json(client, path, payload):
    resp = client.post(path, json=payload)
    text = resp.get_data(as_text=True)
    print(path, resp.status_code, text)
    return resp


def _submit_zip(client, room_code, display_name, password, zip_buf):
    zip_buf.seek(0)
    data = {
        "display_name": display_name,
        "password": password,
        "bot_zip_file": (zip_buf, "bot.zip"),
    }
    resp = client.post(
        f"/api/rooms/{room_code}/submit",
        data=data,
        content_type="multipart/form-data",
    )
    text = resp.get_data(as_text=True)
    print(f"submit:{display_name}", resp.status_code, text)
    return resp


def _get_json(client, path):
    resp = client.get(path)
    text = resp.get_data(as_text=True)
    print(path, resp.status_code, text)
    return resp


def main():
    print("--- Submit Scheduler Flow Test ---")
    _ensure_fresh_database()

    from server.webapp.app import app

    client = app.test_client()

    create_resp = _post_json(client, "/api/rooms", {"game_key": "tron"})
    assert create_resp.status_code == 201, "Failed to create room"
    room = create_resp.get_json()
    room_code = room["room_code"]
    print(f"Room created: {room_code}")

    participants = [
        ("RandomBot", "pw-random", _zip_bot(_random_bot_code())),
        ("GreedyBot", "pw-greedy", _zip_bot(_greedy_bot_code())),
        ("SpaceFillerBot", "pw-space", _zip_bot(_space_filler_bot_code())),
    ]

    for name, _, _ in participants:
        join_resp = _post_json(client, f"/api/rooms/{room_code}/join", {"display_name": name})
        assert join_resp.status_code == 200, f"Join failed for {name}"

    for name, password, bot_zip in participants:
        submit_resp = _submit_zip(client, room_code, name, password, bot_zip)
        assert submit_resp.status_code == 200, f"Submit failed for {name}"

    print("Submissions complete; polling ranked background progress...")

    start = time.time()
    last_match_count = 0
    while time.time() - start < 90:
        time.sleep(3)

        recent_resp = _get_json(client, f"/api/rooms/{room_code}/matches/recent?limit=20")
        lb_resp = _get_json(client, f"/api/rooms/{room_code}/leaderboard")
        if recent_resp.status_code != 200 or lb_resp.status_code != 200:
            continue

        matches = recent_resp.get_json() or []
        leaderboard = lb_resp.get_json() or []
        last_match_count = len(matches)

        non_default = [row for row in leaderboard if int(row.get("rating", 1500)) != 1500]
        print(
            f"poll: matches={len(matches)} non_default_ratings={len(non_default)} "
            f"ratings={[row.get('rating') for row in leaderboard]}"
        )

        if len(matches) >= 2 and non_default:
            print("SUCCESS: background ranked matching is active and ratings are moving.")
            print(json.dumps({"room_code": room_code, "matches": matches[:3], "leaderboard": leaderboard}, indent=2))
            return

    raise RuntimeError(
        f"Timed out waiting for ranked background progress. Last observed match count={last_match_count}. "
        "Check Redis/server logs for scheduler and worker activity."
    )


if __name__ == "__main__":
    main()
