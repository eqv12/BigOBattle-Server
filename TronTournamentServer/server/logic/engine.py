# FINAL FIX: This version includes a sys.path modification at the top,
# making it directly runnable and bypassing the fragile '-m' module system.

import sys
import os
import subprocess
import json
import random
import threading
import queue
import time

# --- BOILERPLATE TO MAKE SCRIPT RUNNABLE ---
# This block of code adds the project's root directory to the Python path.
# This makes the absolute imports (like 'from server.config...') work
# even when the script is executed directly.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
# -------------------------------------------

# Now the absolute imports will work correctly
from server.config import (
    DOCKER_IMAGE_NAME, MOVE_TIMEOUT_S, MEMORY_LIMIT_MB,
    GRID_WIDTH, GRID_HEIGHT, MAX_TURNS
)
from server.logic.game_state import GameState, Player

REPLAYS_DIR = "replays"
os.makedirs(REPLAYS_DIR, exist_ok=True)


def _bot_reader_thread(process, move_queue):
    try:
        for line in iter(process.stdout.readline, b''):
            move_queue.put(line.decode('utf-8').strip())
    except Exception:
        pass


def run_match(bot1_path, bot2_path, match_id):
    print(f"[Match {match_id}] Starting: {os.path.basename(bot1_path)} vs {os.path.basename(bot2_path)}")
    replay_filename = f"{match_id}_replay.json"
    winner_id = -1
    replay_filepath = os.path.join(REPLAYS_DIR, f"{match_id}.json")

    def create_docker_command(bot_path):
        bot_dir = os.path.dirname(bot_path)
        abs_path = os.path.abspath(bot_dir)
        return [
            "docker", "run", "--rm", "-i",
            f'--memory={MEMORY_LIMIT_MB}m', f'--memory-swap={MEMORY_LIMIT_MB}m',
            "-v", f"{abs_path}:/usr/src/app",
            DOCKER_IMAGE_NAME, "/bin/bash", "run.sh"
        ]

    p1_process = subprocess.Popen(create_docker_command(bot1_path), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p2_process = subprocess.Popen(create_docker_command(bot2_path), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    bot_processes = [p1_process, p2_process]
    p1_queue = queue.Queue()
    p2_queue = queue.Queue()
    bot_queues = [p1_queue, p2_queue]
    p1_thread = threading.Thread(target=_bot_reader_thread, args=(p1_process, p1_queue))
    p2_thread = threading.Thread(target=_bot_reader_thread, args=(p2_process, p2_queue))
    p1_thread.daemon = True
    p2_thread.daemon = True
    p1_thread.start()
    p2_thread.start()
    # winner_id = -1
    # replay_filepath = os.path.join(REPLAYS_DIR, f"{match_id}.json")

    try:
        padding = 5
        p1_x = random.randint(padding, (GRID_WIDTH // 2) - padding)
        p1_y = random.randint(padding, GRID_HEIGHT - 1 - padding)
        p2_x = GRID_WIDTH - 1 - p1_x
        p2_y = GRID_HEIGHT - 1 - p1_y
        
        player1 = Player(0, p1_x, p1_y)
        player2 = Player(1, p2_x, p2_y)
        state = GameState([player1, player2])
        turn = 0

        while len([p for p in state.players if p.is_alive]) > 1:
            if turn >= MAX_TURNS:
                print(f"[Match {match_id}] Max turn limit reached.")
                break

            current_player_index = turn % 2
            current_player = state.players[current_player_index]
            process = bot_processes[current_player_index]
            move_queue = bot_queues[current_player_index]

            if not current_player.is_alive:
                turn += 1
                continue

            move = "TIMEOUT"
            try:
                input_str = state.to_json_for_player(current_player.id, turn)
                process.stdin.write(input_str.encode('utf-8'))
                process.stdin.flush()
                raw_output = move_queue.get(timeout=MOVE_TIMEOUT_S)
                try:
                    move_data = json.loads(raw_output)
                    if "move" in move_data and move_data["move"] in ["UP", "DOWN", "LEFT", "RIGHT"]:
                        move = move_data["move"]
                    else:
                        raise ValueError("Invalid move key or value in JSON")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"[Match {match_id}] Player {current_player.id} sent invalid JSON: {e}", file=sys.stderr)
                    move = "CRASH"
            except queue.Empty:
                print(f"[Match {match_id}] Player {current_player.id} timed out!", file=sys.stderr)
            except Exception as e:
                print(f"[Match {match_id}] Player {current_player.id} crashed or had pipe error: {e}", file=sys.stderr)
                move = "CRASH"
            
            state.update_player_move(current_player.id, move)
            turn += 1

        alive_players = [p for p in state.players if p.is_alive]
        if len(alive_players) == 1:
            winner_id = alive_players[0].id
        elif len(alive_players) > 1:
            p0_territory = state.count_territory(0)
            p1_territory = state.count_territory(1)
            if p0_territory > p1_territory: winner_id = 0
            elif p1_territory > p0_territory: winner_id = 1
            else: winner_id = 0
        else:
            winner_id = -1
        
        log_data = state.get_log_data(winner_id)
        replay_data_string = json.dumps(log_data)
        with open(replay_filepath, "w") as f: json.dump(log_data, f)
        print(f"[Match {match_id}] Replay saved to {replay_filepath}")
    except Exception as e:
        # 2. This block CATCHES any error and PREVENTS the crash.
        print(f"[Match {match_id}] A fatal error occurred: {e}")
        # The function will now continue on, using the default error values we set above.

    finally:
        for p in bot_processes:
            try: p.kill()
            except: pass

    print(f"[Match {match_id}] Finished. Winner: Player {winner_id}")
    return winner_id, replay_data_string

# This block allows the script to be run directly for testing
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: py {sys.argv[0]} <path_to_bot_1> <path_to_bot_2> <match_id>")
        sys.exit(1)
    
    bot1 = sys.argv[1]
    bot2 = sys.argv[2]
    match_id = sys.argv[3]
    run_match(bot1, bot2, match_id)

