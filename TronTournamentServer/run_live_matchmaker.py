# In run_live_matchmaker.py (replace the existing function and adjust main)
import time
import math
from server.logic import matchmaker
from server.database import db_handler
from server import config

print("--- SCRIPT TOP LEVEL ---") # PRINT 1


RD_SCALE = 173.7178  # 400 / log(10)

def _g(phi):
    return 1.0 / math.sqrt(1.0 + 3.0 * phi * phi / (math.pi**2))

def _mu(r):
    return (r - 1500.0) / RD_SCALE

def _phi(rd):
    return rd / RD_SCALE

def find_opponent_for(player, all_players, use_info=True):
    """
    Pragmatic, robust opponent picker.

    Rules enforced:
      - no self-play
      - respect rating window (config.MATCHMAKING_RATING_WINDOW)
      - avoid rematches (db_handler.have_teams_played_before)
      - if player is in calibration, prefer calibrated opponents WHEN ANY exist;
        otherwise allow uncalibrated opponents (bootstrap)
      - choose opponent that maximizes the cheap info metric (g^2 * E * (1-E)),
        falling back to closest-rating if info is disabled or inconclusive.

    Returns:
      - opponent dict on success
      - None if no valid opponent found
    """
    import math

    RD_SCALE = 173.7178  # 400 / ln(10)
    def _g(phi):
        return 1.0 / math.sqrt(1.0 + 3.0 * phi * phi / (math.pi**2))
    def _mu(r):
        return (r - 1500.0) / RD_SCALE
    def _phi(rd):
        return rd / RD_SCALE

    player_id = player['id']
    player_rating = player.get('rating', 1500.0)
    player_rd = player.get('rd', getattr(config, 'DEFAULT_RD', 350.0))
    player_is_in_calibration = player.get('matches_played', 0) < config.CALIBRATION_MATCHES

    # --- gather potential opponents under basic rules ---
    potential_opponents = []
    for opp in all_players:
        if opp['id'] == player_id:
            continue
        if abs(player_rating - opp.get('rating', 1500.0)) > config.MATCHMAKING_RATING_WINDOW:
            continue
        if db_handler.have_teams_played_before(player_id, opp['id']):
            continue
        potential_opponents.append(opp)

    if not potential_opponents:
        return None

    # --- prefer calibrated opponents when player is calibrating and such opponents exist ---
    calibrated_opponents = [o for o in potential_opponents if o.get('matches_played', 0) >= config.CALIBRATION_MATCHES]
    if player_is_in_calibration and calibrated_opponents:
        selection_pool = calibrated_opponents
    else:
        selection_pool = potential_opponents

    if not selection_pool:
        return None

    # --- information-aware selection (cheap) ---
    if use_info:
        mu_p = _mu(player_rating)
        best = None
        best_score = -1.0
        EPS = 1e-12

        for o in selection_pool:
            r_o = o.get('rating', 1500.0)
            rd_o = o.get('rd', getattr(config, 'DEFAULT_RD', 350.0))
            mu_o = _mu(r_o)
            phi_o = _phi(rd_o)
            g_o = _g(phi_o)

            # expected score of player vs opponent (Glicko-2)
            # guard against overflow in extreme exponentials
            x = -g_o * (mu_p - mu_o)
            try:
                E = 1.0 / (1.0 + math.exp(x))
            except OverflowError:
                E = 0.0 if x > 0 else 1.0

            info = (g_o * g_o) * E * (1.0 - E)

            # choose highest info; tie-break by rating closeness
            if best is None or info > best_score + EPS:
                best = o
                best_score = info
            elif abs(info - best_score) <= EPS:
                if abs(r_o - player_rating) < abs(best.get('rating', 1500.0) - player_rating):
                    best = o
                    best_score = info

        if best:
            return best

    # --- fallback: closest rating in the chosen pool ---
    selection_pool.sort(key=lambda o: abs(o.get('rating', 1500.0) - player_rating))
    return selection_pool[0]



def main():
    print("--- MAIN FUNCTION STARTED ---") # PRINT 2
    print("🚀 Starting Live Matchmaking System...")
    match_queue = matchmaker.start_matchmaker()
    print("Matchmaker process started successfully.") # PRINT 3


    # This is the main "forever" loop of the matchmaker
    while True:
        print("\n--- Matchmaker Tick ---")

        # Get the pool once
        all_eligible_players = db_handler.get_teams_for_matchmaking()
        if not all_eligible_players:
            print("No players available. Waiting...")
            time.sleep(10)
            continue

        # Ensure the list is sorted by RD DESC for the fallback priority (if you rely on that)
        # all_eligible_players.sort(key=lambda p: p.get('rd', 0.0), reverse=True)
        all_eligible_players.sort(key=lambda p: p['rd'], reverse=True)

        player_to_match = None

        # Priority 1: Find a player who needs calibration.
        for player in all_eligible_players:
            # if player.get('matches_played', 0) < config.CALIBRATION_MATCHES:
            if player['matches_played'] < config.CALIBRATION_MATCHES:
                player_to_match = player
                print(f"Prioritizing calibration for: {player_to_match['name']} ({player_to_match['matches_played']}/{config.CALIBRATION_MATCHES})")
                break  # Stop after finding the first one

        # Priority 2: If no one needs calibration, find a general match.
        if not player_to_match and all_eligible_players:
            player_to_match = all_eligible_players[0]
            print(f"No bots in calibration. Finding general match for: {player_to_match['name']} (RD: {player_to_match['rd']:.2f})")
        
        if not player_to_match:
            # This happens if the player list was empty to begin with.
            time.sleep(30)
            continue

        # Reserve the team in DB to avoid double-scheduling (recommended; implement if you can)
        # db_handler.reserve_team_for_matchmaking(player_to_match['id'])

        # --- Step 2: Find a suitable opponent for that player ---
        opponent = find_opponent_for(player_to_match, all_eligible_players)

        # --- Step 3: If a pair is found, queue the match ---
        if opponent:
            print(f"✅ Found a match: {player_to_match['name']} vs {opponent['name']}")
            match_request = {
                'team_a_id': player_to_match['id'],
                'team_b_id': opponent['id'],
                'is_ranked': True,
                'round': -1
            }
            match_queue.put(match_request)
            # Optionally mark them as queued in DB:
            # db_handler.mark_teams_queued(player_to_match['id'], opponent['id'])
        else:
            print(f"Could not find a suitable opponent for {player_to_match['name']}.")

        time.sleep(5)


if __name__ == "__main__":
    main()