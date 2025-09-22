# In server/logic/matchmaker.py

from server.database import db_handler
from server.logic import engine, rating_system

def run_single_match(team_a_id, team_b_id):
    """
    Runs a single match, updates ratings and stats, and releases the teams.
    This is a simple, serial, non-parallel version.
    """
    print(f"--- Running Match: Team {team_a_id} vs Team {team_b_id} ---")
    
    # Reserve teams to mark them as busy
    if not db_handler.reserve_teams(team_a_id, team_b_id):
        print(f"Could not run match; one or both teams were already reserved.")
        return

    try:
        team0 = db_handler.get_team_by_id(team_a_id)
        team1 = db_handler.get_team_by_id(team_b_id)

        if not (team0 and team1 and team0['active_bot_path'] and team1['active_bot_path']):
            print(f"❌ ERROR: Could not find one or both bots for match. Skipping.")
            return

        match_id = db_handler.create_match(team_a_id, team_b_id)
        match_result = engine.run_match(team0['active_bot_path'], team1['active_bot_path'])
        
        winner_key = match_result['winner']
        winner_team_id = None
        if winner_key == 'p0':
            winner_team_id = team_a_id
        elif winner_key == 'p1':
            winner_team_id = team_b_id

        # Update all database records
        rating_system.update_ratings(team_a_id, team_b_id, winner_key, rating_type='final')
        db_handler.update_match_result(match_id, winner_team_id, match_result['replay'])
        db_handler.update_team_match_stats(team_a_id, team_b_id)
        
        print(f"✅ Finished Match {match_id}: {match_result['termination_reason']}")

    except Exception as e:
        print(f"❌ FATAL ERROR processing match: {e}")
    finally:
        # Always release the teams when done
        db_handler.release_teams(team_a_id, team_b_id)