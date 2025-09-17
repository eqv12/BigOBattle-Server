# This module is the heart of the tournament's backend.
# It manages a pool of worker processes to run matches in parallel.

import multiprocessing
import time
import os

# Use absolute imports to be robust
from server.database import db_handler
from server.logic import engine, rating_system
from server.config import WORKER_PROCESSES, BOTS_DIR

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
            team0_id = match_request['team_a_id']
            team1_id = match_request['team_b_id']
            round_number = match_request['round']
            is_ranked = match_request.get('is_ranked', False) # Default to not ranked
            print(f"[{worker_name}] Picked up match: Team {team0_id} vs Team {team1_id}")

            # --- 1. Get Bot Info from DB ---
            team0 = db_handler.get_team_by_id(team0_id)
            team1 = db_handler.get_team_by_id(team1_id)
            
            # Check if bots exist and have valid paths
            if not (team0 and team1 and team0['active_bot_path'] and team1['active_bot_path']):
                print(f"[{worker_name}] ❌ ERROR: Could not find one or both bots for match. Skipping.")
                continue

            bot0_path = team0['active_bot_path']
            bot1_path = team1['active_bot_path']

            # --- 2. Create Match Record in DB ---
            # This creates the initial record and gives us the unique ID for the replay file.
            match_id = db_handler.create_match(team0_id, team1_id)
            print(f"[{worker_name}] Match created with ID: {match_id}")

            # --- 3. Run the Game Engine ---
            match_result = engine.run_match(bot0_path, bot1_path)

            # 4. Translate the engine's result ('p0' or 'p1') back to the real Team ID
    
            # New logic that passes the raw result to the rating system
            winner_key = match_result['winner'] # This can be 'p0', 'p1', or 'draw'
            replay_data = match_result['replay']

            # Let the rating system handle the outcome, including draws
            # (We assume tournament matches update the 'final' ratings)
            rating_system.update_ratings(team0_id, team1_id, winner_key, rating_type='final')

            # The translation logic is now ONLY needed for saving the match result
            winner_team_id = None
            if winner_key == 'p0':
                winner_team_id = team0_id
            elif winner_key == 'p1':
                winner_team_id = team1_id
            
            # --- 5. Update DB with Final Results ---
            # db_handler.update_team_ratings(team0_id, new_team0_data)
            # db_handler.update_team_ratings(team1_id, new_team1_data)
            termination_reason = match_result['termination_reason'] # Get the reason

            db_handler.update_match_result(match_id, winner_team_id, replay_data=replay_data)
            
            # print(f"[{worker_name}] ✅ Finished processing Match {match_id}. Waiting for next match.")
            print(f"[{worker_name}] ✅ Finished Match {match_id}: {termination_reason}. Waiting for next match.")


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
