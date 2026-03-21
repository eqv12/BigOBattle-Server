import os
import stat
import sqlite3
import shutil

# --- CONFIG ---
BOTS_DIR = "bots"
DB_FILE = "/home/sharun/Documents/Code/Emergent/Emergent-Server/TronTournamentServer/server/database/tournament.db"
NUM_TEAMS = 10 

# --- YOUR WORKING BOT CODE ---
WORKING_BOT_CODE = """import sys
import json
import random

def main():
    # Loop over stdin to handle multiple turns
    for line in sys.stdin:
        try:
            # 1. Parse the Game State
            state = json.loads(line)
            
            width = state["board"]["width"]
            height = state["board"]["height"]
            grid = state["board"]["grid"]
            head = state["you"]["head"]
            
            possible_moves = ["UP", "DOWN", "LEFT", "RIGHT"]
            safe_moves = []

            # 2. Check each move to avoid walls/obstacles
            for move in possible_moves:
                hx, hy = head["x"], head["y"]
                if move == "UP": hy -= 1
                if move == "DOWN": hy += 1
                if move == "LEFT": hx -= 1
                if move == "RIGHT": hx += 1
                
                # Check bounds
                if not (0 <= hx < width and 0 <= hy < height):
                    continue
                
                # Check collisions (anything not '0' is dangerous)
                if grid[hy][hx] != '0':
                    continue
                
                safe_moves.append(move)

            # 3. Choose move
            if safe_moves:
                chosen_move = random.choice(safe_moves)
            else:
                chosen_move = random.choice(possible_moves)

            # 4. Send JSON response (CRITICAL FIX)
            response = {"move": chosen_move}
            print(json.dumps(response))
            sys.stdout.flush()
            
        except Exception as e:
            # If anything breaks, output a random fallback so we don't crash the engine
            # Write error to stderr so we can see it in logs, but keep playing
            sys.stderr.write(str(e))
            print(json.dumps({"move": "UP"}))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
"""

def emergency_setup():
    print("🚨 STARTING EMERGENCY SETUP (USER CODE EDITION) 🚨")

    if not os.path.exists(BOTS_DIR):
        os.makedirs(BOTS_DIR)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for i in range(1, NUM_TEAMS + 1):
        team_name = f"Team-{i}"
        team_folder = os.path.join(BOTS_DIR, team_name)
        os.makedirs(team_folder, exist_ok=True)

        # 1. Write YOUR working Python bot
        with open(os.path.join(team_folder, "bot.py"), "w") as f:
            f.write(WORKING_BOT_CODE)

        # 2. Write the robust run.sh
        # We use $(dirname "$0") to make sure python finds bot.py
        run_script_content = """#!/bin/bash
cd "$(dirname "$0")"
python3 -u bot.py
"""
        run_path = os.path.join(team_folder, "run.sh")
        with open(run_path, "w") as f:
            f.write(run_script_content)

        # 3. Make Executable
        st = os.stat(run_path)
        os.chmod(run_path, st.st_mode | stat.S_IEXEC)

        # 4. Update DB
        db_path = os.path.join("bots", team_name, "run.sh")
        cursor.execute("""
            INSERT INTO teams (name, password_hash, rating, rd, vol, active_bot_path, matches_played, final_rating, final_rd, final_vol)
            VALUES (?, 'dummy_hash', 1500, 350, 0.06, ?, 0, 1500, 350, 0.06)
            ON CONFLICT(name) DO UPDATE SET
                active_bot_path = excluded.active_bot_path,
                matches_played = 0
        """, (team_name, db_path))

        print(f"   ✅ Installed Working Bot: {team_name}")

    # Clear old junk matches
    cursor.execute("DELETE FROM matches")
    cursor.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'matches'")
    
    conn.commit()
    conn.close()
    print("\n🚀 DONE. Your verified code is now installed for all teams.")

if __name__ == "__main__":
    emergency_setup()