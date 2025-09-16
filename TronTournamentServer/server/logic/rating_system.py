import glicko2
from server.database import db_handler

def update_glicko_ratings(winner_id, loser_id):
    """
    Fetches winner and loser ratings, calculates the new ratings using the glicko2
    Player object, and saves them back to the database.
    """
    # 1. Fetch current rating info from the database
    winner_data = db_handler.get_team_by_id(winner_id)
    loser_data = db_handler.get_team_by_id(loser_id)

    print(f"Winner id {winner_id}")
    print(f"Loser id {loser_id}")


    if not winner_data or not loser_data:
        print(f"ERROR: Could not find rating data for match between {winner_id} and {loser_id}")
        return

    # 2. Create Glicko2 Player objects from the database data.
    # We will use the main 'rating' columns for the live leaderboard.
    winner = glicko2.Player(rating=winner_data['rating'], rd=winner_data['rd'], vol=winner_data['vol'])
    loser = glicko2.Player(rating=loser_data['rating'], rd=loser_data['rd'], vol=loser_data['vol'])
    
    # 3. Report the match outcome. The library updates the objects in place.
    # The winner's rating is updated with the loser's stats and a score of 1 (win).
    winner.update_player([loser.getRating()], [loser.getRd()], [1])
    # The loser's rating is updated with the winner's stats and a score of 0 (loss).
    loser.update_player([winner.getRating()], [winner.getRd()], [0])

    # 4. Update the database with the new values from the updated objects.
    db_handler.update_team_ratings(
        team_id=winner_id, 
        new_rating=winner.getRating(),
        new_rd=winner.getRd(),
        new_vol=winner.vol
    )
    db_handler.update_team_ratings(
        team_id=loser_id, 
        new_rating=loser.getRating(),
        new_rd=loser.getRd(),
        new_vol=loser.vol
    )
    
    print(f"Updated Glicko-2 ratings for winner {winner_id} and loser {loser_id}")