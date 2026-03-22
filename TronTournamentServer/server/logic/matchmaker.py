# This module is the heart of the tournament's backend.
# It manages a pool of worker processes to run matches in parallel.

import multiprocessing
import time

# Use absolute imports to be robust
from server.database import db_handler
from server.logic import engine, rating_system
from server.config import WORKER_PROCESSES


def _process_legacy_team_match(match_request, worker_name):
    team0_id = match_request['team_a_id']
    team1_id = match_request['team_b_id']
    print(f"[{worker_name}] Picked up match: Team {team0_id} vs Team {team1_id}")

    team0 = db_handler.get_team_by_id(team0_id)
    team1 = db_handler.get_team_by_id(team1_id)

    if not (team0 and team1 and team0['active_bot_path'] and team1['active_bot_path']):
        print(f"[{worker_name}] ❌ ERROR: Could not find one or both bots for match. Skipping.")
        return

    bot0_path = team0['active_bot_path']
    bot1_path = team1['active_bot_path']

    match_id = db_handler.create_match(team0_id, team1_id)
    print(f"[{worker_name}] Match created with ID: {match_id}")

    match_result = engine.run_match(bot0_path, bot1_path)
    winner_key = match_result['winner']
    replay_data = match_result['replay']

    rating_system.update_ratings(team0_id, team1_id, winner_key, rating_type='final')

    winner_team_id = None
    if winner_key == 'p0':
        winner_team_id = team0_id
    elif winner_key == 'p1':
        winner_team_id = team1_id

    termination_reason = match_result['termination_reason']
    db_handler.update_match_result(match_id, winner_team_id, replay_data=replay_data)
    db_handler.update_team_match_stats(team0_id, team1_id)

    print(f"[{worker_name}] ✅ Finished Match {match_id}: {termination_reason}. Waiting for next match.")


def _process_room_match(match_request, worker_name):
    room_id = match_request['room_id']
    participant_a_id = match_request['participant_a_id']
    participant_b_id = match_request['participant_b_id']

    room = db_handler.get_room_by_code(match_request['room_code']) if match_request.get('room_code') else None
    game_key = match_request.get('game_key') or (room['game_key'] if room else 'tron')

    print(
        f"[{worker_name}] Picked up room match: room={room_id}, "
        f"participants={participant_a_id} vs {participant_b_id}, game={game_key}"
    )

    p0 = db_handler.get_room_participant_by_id(participant_a_id)
    p1 = db_handler.get_room_participant_by_id(participant_b_id)
    if not (p0 and p1 and p0['active_bot_path'] and p1['active_bot_path']):
        print(f"[{worker_name}] ❌ ERROR: Invalid room participant bot paths. Skipping.")
        return

    match_id = db_handler.create_room_match(room_id, game_key, participant_a_id, participant_b_id)
    match_result = engine.run_match(p0['active_bot_path'], p1['active_bot_path'])

    winner_key = match_result['winner']
    replay_data = match_result['replay']
    termination_reason = match_result['termination_reason']

    rating_system.update_room_ratings(room_id, participant_a_id, participant_b_id, winner_key)

    winner_participant_id = None
    if winner_key == 'p0':
        winner_participant_id = participant_a_id
    elif winner_key == 'p1':
        winner_participant_id = participant_b_id

    db_handler.update_room_match_result(match_id, winner_participant_id, replay_data, termination_reason)
    db_handler.update_room_match_stats(room_id, participant_a_id, participant_b_id)

    print(
        f"[{worker_name}] ✅ Finished room match {match_id}: {termination_reason}. "
        f"Waiting for next match."
    )

def run_match_worker(match_queue):
    """
    This is the "recipe" for a single worker process (a "chef").
    It runs in an infinite loop, waiting for matches to appear on the queue,
    processing them one by one.
    """
    # Each worker gets its own unique name for logging
    worker_name = multiprocessing.current_process().name
    print(f"✅ [{worker_name}] Worker started and is waiting for matches.")

    while True:
        try:
            # This is a blocking call. The worker will sleep here until a match is available.
            match_request = match_queue.get()
            queue_type = match_request.get('queue_type', 'legacy')
            if queue_type == 'room':
                _process_room_match(match_request, worker_name)
            else:
                _process_legacy_team_match(match_request, worker_name)


        except Exception as e:
            # This broad exception ensures a single failed match doesn't kill a worker.
            print(f"[{worker_name}] ❌ FATAL ERROR processing a match: {e}")
            # In a production system, you'd have more detailed error logging here.
            time.sleep(1) # Prevent rapid-fire crashes

def start_matchmaker():
    """
    This is the main function to start the entire matchmaking system.
    It will be called once when the server starts.
    """
    print("--- Starting Matchmaking System ---")
    
    # A Manager is needed to create a queue that can be shared between processes.
    manager = multiprocessing.Manager()
    match_queue = manager.Queue()

    # Create a pool of worker processes.
    # The number of workers is loaded from our central config file.
    pool = multiprocessing.Pool(processes=WORKER_PROCESSES)

    print(f"Creating a pool of {WORKER_PROCESSES} worker processes...")
    
    # Assign the worker function to each process in the pool.
    # Each worker will run the 'run_match_worker' function.
    for _ in range(WORKER_PROCESSES):
        pool.apply_async(run_match_worker, (match_queue,))
    
    print("✅ Matchmaking system is running in the background.")
    
    # We return the queue so the Flask web app can add matches to it.
    return match_queue
