import time
import random
from server.database import db_handler

# For your test with 2 bots, we only need 1 round.
# For a full 25-bot tournament, set this to 6 or 7.
NUM_ROUNDS = 3

def pair_teams(round_number, team_ids, scores, played_opponents):
    """Generates pairings for a Swiss tournament round."""
    if round_number == 1:
        # Round 1: Random pairings
        random.shuffle(team_ids)
        # Pair adjacent teams in the shuffled list
        return list(zip(team_ids[0::2], team_ids[1::2]))

    # Round 2+: Pair based on score
    # Group teams by their current score
    score_groups = {}
    for team_id, score in scores.items():
        if score not in score_groups:
            score_groups[score] = []
        score_groups[score].append(team_id)

    pairings = []
    unpaired_players = []

    # Sort groups by score, highest first
    sorted_scores = sorted(score_groups.keys(), reverse=True)
    
    for score in sorted_scores:
        group = score_groups[score]
        random.shuffle(group)
        
        # Add any players who couldn't be paired from a higher group
        group = unpaired_players + group
        unpaired_players = []

        # Pair players within the group, avoiding rematches
        while len(group) >= 2:
            player1 = group.pop(0)
            
            # Find a valid opponent for player1
            opponent_found = False
            for i in range(len(group)):
                player2 = group[i]
                if player2 not in played_opponents[player1]:
                    pairings.append((player1, player2))
                    # Mark that they've played each other
                    played_opponents[player1].add(player2)
                    played_opponents[player2].add(player1)
                    group.pop(i) # Remove the paired opponent
                    opponent_found = True
                    break
            
            if not opponent_found:
                unpaired_players.append(player1)
        
        # Any remaining player "floats down" to the next score group
        unpaired_players.extend(group)

    return pairings


def run_swiss_tournament(match_queue):
    """
    Manages the logic for a full Swiss-style tournament.
    """
    print("🏆 Starting the Swiss Tournament...")

    # 1. Get all teams that have a bot path registered
    playable_teams = db_handler.get_playable_teams()
    if not playable_teams or len(playable_teams) < 2:
        print("❌ Not enough playable teams to start a tournament. Need at least 2.")
        return

    team_ids = [team['id'] for team in playable_teams]
    print(f"Found {len(team_ids)} playable teams.")

    # 2. Initialize scores and opponent tracking
    scores = {team_id: 0 for team_id in team_ids}
    # Initialize with self to prevent playing against oneself
    played_opponents = {team_id: {team_id} for team_id in team_ids}

    # 3. Main tournament loop
    for round_number in range(1, NUM_ROUNDS + 1):
        print(f"\n--- Round {round_number} ---")

        # 4. Generate pairings for the current round
        pairings = pair_teams(round_number, team_ids, scores, played_opponents)
        
        if not pairings:
            print("No valid pairings could be made. Ending tournament.")
            break
            
        print(f"Generated {len(pairings)} pairings for Round {round_number}.")

        # 5. Add all matches for this round to the queue
        for team_a_id, team_b_id in pairings:
            match_request = {
                'team_a_id': team_a_id,
                'team_b_id': team_b_id,
                'round': round_number
            }
            match_queue.put(match_request)
        
        # 6. Wait for the round to complete
        print(f"Waiting for {len(pairings)} matches to complete...")
        while db_handler.count_completed_matches_for_round(round_number) < len(pairings):
            time.sleep(3) # Check the database every 3 seconds

        print("Round complete!")
        
        # 7. Get results and update scores
        results = db_handler.get_results_for_round(round_number)
        for result in results:
            winner_id = result['winner_team_id']
            if winner_id:
                scores[winner_id] += 1
            else: # Handle draws
                scores[result['team_a_id']] += 0.5
                scores[result['team_b_id']] += 0.5

    # 8. Print final standings
    print("\n--- Final Tournament Standings ---")
    # Create a list of (team_name, score)
    final_standings = []
    team_map = {team['id']: team['name'] for team in playable_teams}
    for team_id, score in scores.items():
        final_standings.append((team_map[team_id], score))
    
    # Sort by score, descending
    final_standings.sort(key=lambda x: x[1], reverse=True)
    
    for i, (name, score) in enumerate(final_standings):
        print(f"{i+1}. {name}: {score} points")