import io
import json
import os
import time
from server.database import db_handler
from scripts.active.test_submit_scheduler_flow import (
    _ensure_fresh_database,
    _zip_bot,
    _random_bot_code,
    _greedy_bot_code,
    _space_filler_bot_code,
    _post_json,
    _submit_zip,
    _get_json
)

def main():
    print("--- 30-Bot Scale & Convergence Test ---")
    
    # 1. Setup Data and Room
    _ensure_fresh_database()
    from server.webapp.app import app
    client = app.test_client()

    create_resp = _post_json(client, "/api/rooms", {"game_key": "tron"})
    assert create_resp.status_code == 201, "Failed to create room"
    room = create_resp.get_json()
    room_code = room["room_code"]
    print(f"Room created: {room_code}")

    # 2. Prepare Participants
    participants = []
    
    # 5 SpaceFillers
    for i in range(1, 6):
        participants.append((f"spacefiller{i}", f"pw-sf{i}", _zip_bot(_space_filler_bot_code())))
        
    # 15 Greedys
    for i in range(1, 16):
        participants.append((f"greedy{i}", f"pw-g{i}", _zip_bot(_greedy_bot_code())))
        
    # 10 Randoms
    for i in range(1, 11):
        participants.append((f"random{i}", f"pw-r{i}", _zip_bot(_random_bot_code())))

    print(f"Prepared {len(participants)} bots for submission...")

    # 3. Join Room
    for name, _, _ in participants:
        resp = _post_json(client, f"/api/rooms/{room_code}/join", {"display_name": name})
        assert resp.status_code == 200, f"Join failed for {name}"

    # 4. Configure Workers (Auto-started by app on first submission)
    from server import config
    config.RANKED_WORKER_PROCESSES = 4
    config.TEST_WORKER_PROCESSES = 2
    print("Configured worker pool: 4 Ranked, 2 Test. Will start automatically.")

    # 5. Mass Submit Burst
    print("\nStarting mass submission burst...")
    start_time = time.time()
    for name, password, bot_zip in participants:
        resp = _submit_zip(client, room_code, name, password, bot_zip)
        assert resp.status_code == 200, f"Submit failed for {name}"
    
    submit_duration = time.time() - start_time
    print(f"All {len(participants)} bots submitted in {submit_duration:.2f} seconds.")

    # 6. Polling for Convergence
    print("\nPolling for convergence... (Waiting for all RDs to stabilize)")
    convergence_start = time.time()
    
    room_id = room['id'] if 'id' in room else 1 # Fallback to 1 if not in response
    
    while True:
        time.sleep(5)
        stats = db_handler.get_room_convergence_stats(room_id)
        
        matches_played = db_handler.get_room_matchmaking_stats(room_id).get('total_matches_played', 0)
        
        is_converged = stats.get('is_converged', False)
        calibrating = stats.get('calibrating_participants', 0)
        max_rd = stats.get('max_rd', 0)
        
        print(f"[{time.time() - convergence_start:.1f}s] Matches: {matches_played} | Calibrating Bots: {calibrating} | Max RD: {max_rd:.2f}")
        
        if is_converged:
            print("\n✅ CONVERGENCE REACHED!")
            break
            
        if time.time() - convergence_start > 300: # 5 minute timeout
            print("\n⚠️ TIMEOUT reached before convergence. Ending test.")
            break

    total_time = time.time() - convergence_start
    print(f"Total Matchmaking Time: {total_time:.2f} seconds.")

    # 7. Print Final Leaderboard Output
    print("\n--- FINAL LEADERBOARD ---")
    lb_resp = _get_json(client, f"/api/rooms/{room_code}/leaderboard")
    leaderboard = lb_resp.get_json() or []
    
    print(f"{'Rank':<5} | {'Bot Name':<15} | {'Rating':<7} | {'RD':<5} | {'Matches'}")
    print("-" * 55)
    for pos, row in enumerate(leaderboard, 1):
        name = row.get("display_name", "")
        rating = row.get("rating", 0)
        rd = row.get("rd", 0)
        matches = row.get("matches_played", 0)
        print(f"{pos:<5} | {name:<15} | {rating:<7} | {rd:<5} | {matches}")
        
    print("\nTest completed.")

if __name__ == "__main__":
    main()
