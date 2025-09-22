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
    print("🚀 Starting Serial Matchmaking System...")
    tick_counter = 0
    stuck_counter = 0

    while True:
        print(f"\n--- Matchmaker Tick {tick_counter} ---")
        tick_counter += 1
        
        all_eligible_players = db_handler.get_teams_for_matchmaking()
        if len(all_eligible_players) < 2:
            print("Not enough players to make a match. Waiting...")
            time.sleep(10)
            continue

        match_made = False
        
        # Decide which pool of players to use for this tick
        is_calibration_tick = (tick_counter % (config.MATCHMAKING_RATIO + 1)) != 0
        
        candidate_pool = []
        if is_calibration_tick:
            candidate_pool = [p for p in all_eligible_players if p['matches_played'] < config.CALIBRATION_MATCHES]
            print(f"Mode: Calibration. Candidates: {len(candidate_pool)}")
        else:
            candidate_pool = [p for p in all_eligible_players if p['matches_played'] >= config.CALIBRATION_MATCHES]
            print(f"Mode: General. Candidates: {len(candidate_pool)}")

        # Now, try to find a match using the chosen pool
        if candidate_pool:
            for player in candidate_pool:
                opponent = find_opponent_for(player, all_eligible_players)
                if opponent:
                    matchmaker.run_single_match(player['id'], opponent['id'])
                    match_made = True
                    break # Found one match for this tick, that's enough.
        
        # --- Shutdown logic ---
        if not match_made:
            print("Could not find any suitable matches this tick.")
            # Check if all players have a stable rating.
            all_rds = [p['rd'] for p in all_eligible_players]
            if all(rd < config.STABLE_RD_THRESHOLD for rd in all_rds):
                print(f"\n✅ All active players have a stable RD below {config.STABLE_RD_THRESHOLD}. Shutting down.")
                break
        # --- NEW: Check if the system is stuck ---
        if not match_made:
            stuck_counter += 1
        else:
            stuck_counter = 0 # Reset counter if a match was made

        if stuck_counter >= config.STUCK_TICKS_BEFORE_STOP:
            print(f"\n🚫 No matches found for {config.STUCK_TICKS_BEFORE_STOP} ticks. Assuming system is stuck. Shutting down.")
            break
        # We no longer need a sleep here if we are running at max speed
        # time.sleep(5) 

    print("--- Matchmaking has concluded. ---")

if __name__ == "__main__":
    main()