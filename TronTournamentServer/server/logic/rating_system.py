import glicko2  # type: ignore
from server.database import db_handler

# Replace your old rating update function with this
def update_ratings(p0_team_id, p1_team_id, winner_key, rating_type='live'):
    """
    Calculates and updates ratings for two players based on a match outcome.
    Handles wins, losses, and draws.
    """
    p0_data = db_handler.get_team_by_id(p0_team_id)
    p1_data = db_handler.get_team_by_id(p1_team_id)

    if not p0_data or not p1_data:
        print(f"ERROR: Could not find rating data for match between {p0_team_id} and {p1_team_id}")
        return

    # Determine which set of columns to use
    rating_col, rd_col, vol_col = ('rating', 'rd', 'vol')
    if rating_type == 'final':
        rating_col, rd_col, vol_col = ('final_rating', 'final_rd', 'final_vol')
    
    p0 = glicko2.Player(rating=p0_data[rating_col], rd=p0_data[rd_col], vol=p0_data[vol_col])
    p1 = glicko2.Player(rating=p1_data[rating_col], rd=p1_data[rd_col], vol=p1_data[vol_col])

    # Determine scores based on the outcome
    if winner_key == 'p0':
        p0_score, p1_score = 1.0, 0.0 # p0 wins
    elif winner_key == 'p1':
        p0_score, p1_score = 0.0, 1.0 # p1 wins
    else: # Draw
        p0_score, p1_score = 0.5, 0.5 # Draw

    # Update player objects with the outcome
    # p0.update_player([p1.getRating()], [p1.getRd()], [p1_score])
    # p1.update_player([p0.getRating()], [p0.getRd()], [p0_score])

    # Update player objects with the outcome
    p0.update_player([p1.getRating()], [p1.getRd()], [p0_score])
    p1.update_player([p0.getRating()], [p0.getRd()], [p1_score])

    # Save new ratings back to the database
    db_handler.update_team_ratings(p0_team_id, p0.getRating(), p0.getRd(), p0.vol, rating_type)
    db_handler.update_team_ratings(p1_team_id, p1.getRating(), p1.getRd(), p1.vol, rating_type)

    print(f"Updated {rating_type} ratings for {p0_team_id} and {p1_team_id}.")


def update_room_ratings(room_id, p0_participant_id, p1_participant_id, winner_key):
    """
    Updates room-scoped Glicko-2 ratings for two room participants.
    winner_key: 'p0' | 'p1' | 'draw'
    """
    p0_data = db_handler.get_room_rating(room_id, p0_participant_id)
    p1_data = db_handler.get_room_rating(room_id, p1_participant_id)

    if not p0_data or not p1_data:
        print(
            f"ERROR: Could not find room rating data for room={room_id}, "
            f"participants=({p0_participant_id}, {p1_participant_id})"
        )
        return

    p0 = glicko2.Player(rating=p0_data['rating'], rd=p0_data['rd'], vol=p0_data['vol'])
    p1 = glicko2.Player(rating=p1_data['rating'], rd=p1_data['rd'], vol=p1_data['vol'])

    if winner_key == 'p0':
        p0_score, p1_score = 1.0, 0.0
    elif winner_key == 'p1':
        p0_score, p1_score = 0.0, 1.0
    else:
        p0_score, p1_score = 0.5, 0.5

    p0.update_player([p1.getRating()], [p1.getRd()], [p0_score])
    p1.update_player([p0.getRating()], [p0.getRd()], [p1_score])

    db_handler.update_room_rating(room_id, p0_participant_id, p0.getRating(), p0.getRd(), p0.vol)
    db_handler.update_room_rating(room_id, p1_participant_id, p1.getRating(), p1.getRd(), p1.vol)

    print(
        f"Updated room ratings for room={room_id}, "
        f"participants=({p0_participant_id}, {p1_participant_id})"
    )