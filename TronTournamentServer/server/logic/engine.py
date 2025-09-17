# server/logic/engine.py
import subprocess
import json
import random
import threading
import time
import os
import random

from server.config import DOCKER_IMAGE_NAME, MOVE_TIMEOUT_S, MEMORY_LIMIT_MB, GRID_WIDTH, GRID_HEIGHT, MAX_TURNS, FIRST_MOVE_TIMEOUT_S
from server.logic.game_state import Player, GameState

#function for calculating symmertric positions
def get_symmetric_start_positions(width, height, padding):
    """Calculates a random, symmetrical starting position for two players."""
    # Player 1's position is chosen randomly in the left half of the grid,
    # respecting the padding.
    p1_x = random.randint(padding, (width // 2) - padding)
    p1_y = random.randint(padding, height - 1 - padding)

    # Player 2's position is a mirror image on the right half.
    p2_x = width - 1 - p1_x
    p2_y = p1_y  # Start on the same row for symmetry

    p1_pos = (p1_x, p1_y)
    p2_pos = (p2_x, p2_y)
    
    return p1_pos, p2_pos

def get_bot_response(bot_proc, json_data, timeout_s):
    """Gets a bot's move with a strict time limit."""
    result = {"move": None, "raw_output": "", "error": None}
    
    def target():
        try:
            bot_proc.stdin.write(json_data.encode('utf-8'))
            bot_proc.stdin.flush()
            line = bot_proc.stdout.readline().decode('utf-8').strip()
            result["raw_output"] = line
            if line:
                result["move"] = json.loads(line).get("move")
            else:
                result["error"] = "Bot exited or sent empty response."
        except (IOError, json.JSONDecodeError) as e:
            result["error"] = f"Invalid JSON or I/O Error: {e}"
        except Exception as e:
            result["error"] = f"Unknown bot error: {e}"

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout=timeout_s)

    if thread.is_alive():
        result["error"] = f"Timeout: Move took longer than {timeout_s * 1000}ms."
    
    return result

def create_docker_command(bot_path):
    bot_dir = os.path.dirname(bot_path)
    abs_dir_path = os.path.abspath(bot_dir)
    return [
        "docker", "run", "--rm", "-i",
        f'--memory={MEMORY_LIMIT_MB}m', f'--memory-swap={MEMORY_LIMIT_MB}m',
        "-v", f"{abs_dir_path}:/usr/src/app",
        DOCKER_IMAGE_NAME, "/bin/bash", "run.sh"
    ]

def run_match(bot_path_1, bot_path_2):
    """
    Runs a single, fair Tron match between two bots inside Docker containers.
    This version is based on the simultaneous-move referee logic.
    """
    # p1_proc = subprocess.Popen(create_docker_command(bot_path_1), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # p2_proc = subprocess.Popen(create_docker_command(bot_path_2), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    p1_proc = subprocess.Popen(create_docker_command(bot_path_1), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p2_proc = subprocess.Popen(create_docker_command(bot_path_2), stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    bot_procs = [p1_proc, p2_proc]

    # REFACTORED: Initialize game objects from the new game_state
    # padding = 5
    # p1_x = random.randint(padding, (GRID_WIDTH // 2) - padding)
    # p1_y = random.randint(padding, GRID_HEIGHT - 1 - padding)
    # p2_x = GRID_WIDTH - 1 - p1_x
    # p2_y = p1_y # Start on the same row for symmetry
    # players = [Player(0, (p1_x, p1_y), (1, 0)), Player(1, (p2_x, p2_y), (-1, 0))] # p0, p1

    # Initialize game objects with random, symmetric starting positions.
    padding = 5
    p1_start_pos, p2_start_pos = get_symmetric_start_positions(GRID_WIDTH, GRID_HEIGHT, padding)
    
    # p0 starts on the left moving right, p1 starts on the right moving left.
    players = [Player(0, p1_start_pos, (1, 0)), Player(1, p2_start_pos, (-1, 0))]
    #new logic to start at symmetric random places


    state = GameState(GRID_WIDTH, GRID_HEIGHT)
    
    game_log = {"frames": [], "result": {}}
    turn = 0
    
    game_log["frames"].append(state.get_state_for_json(turn, players[0], players[1]))

    winner_id_num = -1 # -1 for draw, 0 for p0, 1 for p1
    termination_reason = "Max turns reached"

    while all(p.is_alive for p in players) and turn < MAX_TURNS:
        turn += 1
        
        # 1. Get moves from both bots simultaneously
        p0_json = state.get_json_for_bot(turn, players[0], players[1])
        p1_json = state.get_json_for_bot(turn, players[1], players[0])

        current_timeout = FIRST_MOVE_TIMEOUT_S if turn == 1 else MOVE_TIMEOUT_S

        p0_response = get_bot_response(bot_procs[0], p0_json, current_timeout) #changed this from MOVE_TIMEOUT_S to current time out to include jvm startup time
        p1_response = get_bot_response(bot_procs[1], p1_json, current_timeout)

        p0_move, p1_move = p0_response["move"], p1_response["move"]

        # 2. Disqualify bots for errors/timeouts/invalid moves
        move_map = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
        if p0_response["error"] or p0_move not in move_map:
            players[0].is_alive = False
            termination_reason = f"p0 error: {p0_response['error'] or 'Invalid move'}"
        if p1_response["error"] or p1_move not in move_map:
            players[1].is_alive = False
            termination_reason = f"p1 error: {p1_response['error'] or 'Invalid move'}"

        if not all(p.is_alive for p in players): break

        # 3. Set intended directions
        players[0].direction = move_map[p0_move]
        players[1].direction = move_map[p1_move]

        # 4. Check for all collisions *before* moving
        state.check_for_fatalities(players[0], players[1])
        if not players[0].is_alive and not players[1].is_alive: termination_reason = "Head-on collision or mutual error"
        elif not players[0].is_alive: termination_reason = "p0 collision"
        elif not players[1].is_alive: termination_reason = "p1 collision"

        # 5. Apply moves for any players still alive
        if players[0].is_alive: players[0].apply_move()
        if players[1].is_alive: players[1].apply_move()
        
        game_log["frames"].append(state.get_state_for_json(turn, players[0], players[1]))

    # --- End of Loop ---

    # Determine winner
    p0_alive, p1_alive = players[0].is_alive, players[1].is_alive
    winner_key = "draw"
    if p0_alive and not p1_alive: winner_key, winner_id_num = "p0", 0
    elif not p0_alive and p1_alive: winner_key, winner_id_num = "p1", 1
    
    # Finalize log and kill processes
    game_log["result"] = {"winner": winner_key, "termination": termination_reason}
    replay_data_string = json.dumps(game_log)
    for proc in bot_procs:
        try: proc.kill()
        except: pass

    # REFACTORED: Return the standard result dictionary
    return {
        "winner": winner_key,
        "replay": replay_data_string,
        "termination_reason": termination_reason
    }