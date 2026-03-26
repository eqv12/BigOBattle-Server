# server/logic/engine.py
import subprocess
import json
import random
import threading
import os

from server.config import DOCKER_IMAGE_NAME, MOVE_TIMEOUT_S, MEMORY_LIMIT_MB, MAX_TURNS, FIRST_MOVE_TIMEOUT_S
from server.engine.referee import run_referee_match
from server.games.base import MatchConfig
from server.games.tron import TronPlugin


def _consume_stream(stream, bucket):
    while True:
        line = stream.readline()
        if not line:
            break
        bucket.append(line.decode('utf-8', errors='replace').rstrip('\n'))

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
                bot_proc.poll()
                rc = bot_proc.returncode
                if rc == 137 or rc == -9:
                    result["error"] = "OOM: Memory limit exceeded."
                elif rc is not None:
                    result["error"] = f"Bot exited unexpectedly with code {rc}."
                else:
                    result["error"] = "Bot exited or sent empty response."
        except (IOError, json.JSONDecodeError) as e:
            bot_proc.poll()
            rc = bot_proc.returncode
            if rc == 137 or rc == -9:
                result["error"] = "OOM: Memory limit exceeded."
            else:
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
    p1_proc = subprocess.Popen(
        create_docker_command(bot_path_1),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p2_proc = subprocess.Popen(
        create_docker_command(bot_path_2),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    bot_procs = [p1_proc, p2_proc]
    player_errors = {}
    turn_counter = {"value": 0}
    stderr_lines = {0: [], 1: []}
    turn_events = {}

    stderr_threads = [
        threading.Thread(target=_consume_stream, args=(p1_proc.stderr, stderr_lines[0]), daemon=True),
        threading.Thread(target=_consume_stream, args=(p2_proc.stderr, stderr_lines[1]), daemon=True),
    ]
    for t in stderr_threads:
        t.start()

    def _get_action(player_index, bot_view_json):
        current_timeout = FIRST_MOVE_TIMEOUT_S if turn_counter["value"] == 0 else MOVE_TIMEOUT_S
        response = get_bot_response(bot_procs[player_index], bot_view_json, current_timeout)

        turn_no = max(1, turn_counter["value"])
        event = turn_events.setdefault(turn_no, {})
        event[f"p{player_index}_stdout"] = response.get("raw_output", "")
        event[f"p{player_index}_move"] = response.get("move")

        if response["error"]:
            envelope = {
                "type": "timeout" if "Timeout" in response["error"] else ("oom" if "OOM" in response["error"] else "runtime"),
                "message": response["error"],
                "turn": turn_no,
                "stdout_snippet": response.get("raw_output", "")[:200]
            }
            player_errors[player_index] = envelope
            event[f"p{player_index}_error"] = response["error"]
            return None
        return response["move"]

    plugin = TronPlugin()
    seed = random.randint(0, 2**31 - 1)
    match_config = MatchConfig(seed=seed, max_turns=MAX_TURNS)

    try:
        def _step(player_index, bot_view_json):
            # Step counter increments once per turn when p0 requests action.
            if player_index == 0:
                turn_counter["value"] += 1
            return _get_action(player_index, bot_view_json)

        referee_result = run_referee_match(plugin, match_config, _step)

        error_envelope = {}
        termination_reason = referee_result.termination_reason

        for p_idx in (0, 1):
            if player_errors.get(p_idx):
                env = player_errors[p_idx]
                env["stderr_snippet"] = "\n".join(stderr_lines[p_idx][-20:]) # last 20 lines
                error_envelope[f"p{p_idx}"] = env

        if error_envelope:
            err_strs = []
            if "p0" in error_envelope:
                err_strs.append(f"p0 error: {error_envelope['p0']['message']}")
            if "p1" in error_envelope:
                err_strs.append(f"p1 error: {error_envelope['p1']['message']}")
            termination_reason = " | ".join(err_strs)

        replay = json.loads(referee_result.replay)
        replay["result"]["termination"] = termination_reason
        if error_envelope:
            replay["result"]["error_envelope"] = error_envelope

        replay["result"]["turn_events"] = [
            {"turn": turn_no, **turn_events[turn_no]}
            for turn_no in sorted(turn_events.keys())
        ]
        replay["result"]["bot_raw_outputs"] = {
            "p0": {
                "stderr": stderr_lines[0],
            },
            "p1": {
                "stderr": stderr_lines[1],
            },
        }

        return {
            "winner": referee_result.winner,
            "replay": json.dumps(replay),
            "termination_reason": termination_reason,
        }
    finally:
        for proc in bot_procs:
            try:
                proc.kill()
            except Exception:
                pass
        for t in stderr_threads:
            t.join(timeout=0.15)