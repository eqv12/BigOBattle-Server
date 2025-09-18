# In run_live_matchmaker.py

import time
import math
from server.logic import matchmaker
from server.database import db_handler
from server import config

# --- Glicko-2 Helper Constants & Functions ---
RD_SCALE = 173.7178  # This is 400 / log(10)

def _g(phi):
    return 1.0 / math.sqrt(1.0 + 3.0 * phi * phi / (math.pi**2))

def _mu(r):
    return (r - 1500.0) / RD_SCALE

def _phi(rd):
    return rd / RD_SCALE

def find_opponent_for(player, all_players):
    """
    Finds the most informative opponent for a given player while respecting
    matchmaking rules.
    """
    player_rating = player['rating']
    player_is_in_calibration = player.get('matches_played', 0) < config.CALIBRATION_MATCHES
    
    potential_opponents = []
    for opponent in all_players:
        # Rule 1: Don't play against yourself.
        if player['id'] == opponent['id']:
            continue
        # Rule 2: Only play within the rating window.
        if abs(player_rating - opponent['rating']) > config.MATCHMAKING_RATING_WINDOW:
            continue
        # Rule 3: Avoid rematches.
        if db_handler.have_teams_played_before(player['id'], opponent['id']):
            continue
        # Rule 4: When calibrating, prefer calibrated opponents.
        opponent_is_calibrated = opponent.get('matches_played', 0) >= config.CALIBRATION_MATCHES
        if player_is_in_calibration and not opponent_is_calibrated:
            continue
        
        potential_opponents.append(opponent)

    if not potential_opponents:
        return None

    # --- Information-based selection ---
    mu_p = _mu(player_rating)
    best_opponent = None
    max_info = -1.0

    for opponent in potential_opponents:
        mu_o = _mu(opponent['rating'])
        phi_o = _phi(opponent.get('rd', 350.0))
        g_o = _g(phi_o)
        
        expected_score = 1.0 / (1.0 + math.exp(-g_o * (mu_p - mu_o)))
        information = (g_o**2) * expected_score * (1.0 - expected_score)

        if information > max_info:
            max_info = information
            best_opponent = opponent
            
    return best_opponent

def main():
    print("🚀 Starting Live Matchmaking System...")
    match_queue = matchmaker.start_matchmaker()

    while True:
        print("\n--- Matchmaker Tick ---")

        all_eligible_players = db_handler.get_teams_for_matchmaking()
        if not all_eligible_players:
            print("No players available. Waiting...")
            time.sleep(10)
            continue

        player_to_match = None

        # Priority 1: Find a player who needs calibration.
        for player in all_eligible_players:
            if player.get('matches_played', 0) < config.CALIBRATION_MATCHES:
                player_to_match = player
                print(f"Prioritizing calibration for: {player['name']} ({player['matches_played']}/{config.CALIBRATION_MATCHES})")
                break

        # Priority 2: If no one needs calibration, find a general match.
        if not player_to_match:
            # The list is already sorted by RD DESC from the db_handler
            player_to_match = all_eligible_players[0]
            print(f"No bots in calibration. Finding general match for: {player_to_match['name']} (RD: {player_to_match.get('rd', 0.0):.2f})")
        
        if not player_to_match:
            time.sleep(10)
            continue

        opponent = find_opponent_for(player_to_match, all_eligible_players)

        if opponent:
            print(f"✅ Found a match: {player_to_match['name']} vs {opponent['name']}")
            match_request = {
                'team_a_id': player_to_match['id'],
                'team_b_id': opponent['id'],
                'is_ranked': True,
                'round': -1
            }
            match_queue.put(match_request)
        else:
            print(f"Could not find a suitable opponent for {player_to_match['name']}.")

        time.sleep(5)

if __name__ == "__main__":
    main()