# In run_live_matchmaker.py

import time
from server.logic import matchmaker
from server.database import db_handler
from server import config

def find_opponent_for(player, all_players):
    """
    Finds a suitable opponent for a given player based on a set of rules.
    """
    player_rating = player['rating']
    player_is_in_calibration = player['matches_played'] < config.CALIBRATION_MATCHES
    
    potential_opponents = []

    for opponent in all_players:
        # Rule 1: Don't play against yourself.
        if player['id'] == opponent['id']:
            continue

        # Rule 2: Only play against opponents within the rating window.
        rating_difference = abs(player_rating - opponent['rating'])
        if rating_difference > config.MATCHMAKING_RATING_WINDOW:
            continue

        # Rule 3: Avoid rematches.
        if db_handler.have_teams_played_before(player['id'], opponent['id']):
            continue
            
        # Rule 4: If the player is in calibration, they should prefer a calibrated opponent.
        opponent_is_calibrated = opponent['matches_played'] >= config.CALIBRATION_MATCHES
        if player_is_in_calibration and not opponent_is_calibrated:
            continue # Skip other uncalibrated bots if you are calibrating

        potential_opponents.append(opponent)

    # If we found any valid opponents, pick the one with the closest rating.
    if not potential_opponents:
        return None
    else:
        # Sort potential opponents by how close their rating is to the player's.
        potential_opponents.sort(key=lambda o: abs(player_rating - o['rating']))
        return potential_opponents[0]

def main():
    print("🚀 Starting Live Matchmaking System...")
    match_queue = matchmaker.start_matchmaker()

    # This is the main "forever" loop of the matchmaker
    while True:
        print("\n--- Matchmaker Tick ---")
        
        # --- Step 1: Find a player who needs a match ---
        all_eligible_players = db_handler.get_teams_for_matchmaking()
        player_to_match = None

        # Priority 1: Find a player who needs calibration.
        for player in all_eligible_players:
            if player['matches_played'] < config.CALIBRATION_MATCHES:
                player_to_match = player
                print(f"Prioritizing calibration for: {player_to_match['name']} ({player['matches_played']}/{config.CALIBRATION_MATCHES})")
                break # Stop after finding the first one

        # Priority 2: If no one needs calibration, find a general match.
        if not player_to_match and all_eligible_players:
            # The list is already sorted by RD DESC, so the first player is our target.
            player_to_match = all_eligible_players[0]
            print(f"No bots in calibration. Finding general match for: {player_to_match['name']} (RD: {player_to_match['rd']:.2f})")
        
        player_to_match = None # Placeholder
        
        if not player_to_match:
            print("No players available or needing a match. Waiting...")
            time.sleep(10)
            continue # Go to the next loop iteration

        # --- Step 2: Find a suitable opponent for that player ---
        all_players = db_handler.get_teams_for_matchmaking()
        opponent = find_opponent_for(player_to_match, all_players)

        # --- Step 3: If a pair is found, queue the match ---
        if opponent:
            print(f"✅ Found a match: {player_to_match['name']} vs {opponent['name']}")
            match_request = {
                'team_a_id': player_to_match['id'],
                'team_b_id': opponent['id'],
                'is_ranked': True, # All live matches are ranked
                'round': -1 # Using -1 to signify a live match, not a tournament round
            }
            match_queue.put(match_request)
        else:
            print(f"Could not find a suitable opponent for {player_to_match['name']}.")

        # Wait for a bit before the next cycle
        time.sleep(5)

if __name__ == "__main__":
    main()