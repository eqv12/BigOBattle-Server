# In run_final.py
import os
import time
from server.database import db_handler, db_setup
from run_live_matchmaker import main as run_matchmaking

# --- DEFINE YOUR DESIRED OUTCOME HERE ---
TARGET_RANKING = [
    "Team-1",
    "Team-9",
    "Team-12",
]
# -----------------------------------------

def reset_simulation_state():
    """
    Resets the database state for a new simulation run using SQL commands.
    This is much faster than deleting and recreating the DB file.
    """
    print("- Resetting database state for new run...")
    conn = db_handler.get_db_connection()
    cur = conn.cursor()
    
    # Clear old match history
    cur.execute("DELETE FROM matches;")
    cur.execute("DELETE FROM sqlite_sequence WHERE name='matches';")
    
    # Reset team stats and ratings back to their defaults
    cur.execute("""
        UPDATE teams SET
            final_rating = 1500,
            final_rd = 350,
            final_vol = 0.06,
            matches_played = 0,
            is_playing = 0,
            last_played_at = NULL;
    """)
    
    conn.commit()
    conn.close()

def get_final_ranking():
    """Queries the DB and returns the final ranked list of team names."""
    teams = db_handler.get_teams_for_matchmaking()
    teams.sort(key=lambda t: t['rating'], reverse=True)
    return [t['name'] for t in teams]

def main_looper():
    run_count = 0
    # Make sure all bots are submitted before starting the loop.
    print("Starting simulation. Ensure all bots are submitted.")
    
    while True:
        run_count += 1
        print(f"\n\n{'='*20} STARTING SIMULATION RUN #{run_count} {'='*20}")
        
        # 1. Reset the simulation state using SQL
        reset_simulation_state()
        
        # 2. Run the entire matchmaking process to completion
        run_matchmaking()
        
        # 3. Check the result
        final_ranking = get_final_ranking()
        print("\n--- SIMULATION COMPLETE ---")
        print(f"Final Ranking: {final_ranking}")
        
        # Get the number of ranks we need to check (e.g., 3)
        num_ranks_to_check = len(TARGET_RANKING)

        # Compare only the top part of the list
        if final_ranking[:num_ranks_to_check] == TARGET_RANKING:
            print(f"\n\n🎉 SUCCESS! Desired ranking achieved after {run_count} runs.")
            break
        else:
            print(f"Incorrect ranking. Retrying...")
            time.sleep(1)

if __name__ == "__main__":
    main_looper()