import sqlite3
import datetime
from server.config import DATABASE_FILE
import hashlib
import time

# This helper function should be here so we can use it for verification.
def hash_password(password):
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_team_by_name(team_name):
    """Finds a single team by their unique name."""
    conn = get_db_connection()
    team = conn.execute('SELECT * FROM teams WHERE name = ?', (team_name,)).fetchone()
    conn.close()
    return team

def verify_team_credentials(team_name, password):
    """
    Verifies if the provided password is correct for the given team name.
    Returns True if valid, False otherwise.
    """
    team = get_team_by_name(team_name)
    if not team:
        return False # Team does not exist

    # Hash the submitted password and compare it to the stored hash.
    submitted_password_hash = hash_password(password)
    
    return submitted_password_hash == team['password_hash']

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    # check_same_thread=False is important for our multi-process matchmaker
    conn.row_factory = sqlite3.Row
    return conn

def get_team_by_id(team_id):
    """Finds a single team by their unique ID."""
    conn = get_db_connection()
    team = conn.execute('SELECT * FROM teams WHERE id = ?', (team_id,)).fetchone()
    conn.close()
    # return team
    # Also convert this to a dictionary if a team was found
    return dict(team) if team else None

def update_team_status(team_id, new_status):
    """Updates a team's status after their calibration match ('verified' or 'error')."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE teams SET status = ? WHERE id = ?', (new_status, team_id))
    conn.commit()
    conn.close()
    print(f"Updated status for Team ID {team_id} to '{new_status}'")

def update_team_ratings(team_id, new_rating, new_rd, new_vol, rating_type='live'):
    """
    Updates a team's Glicko-2 ratings in the correct columns based on rating_type.
    """
    
    # The 'rating_type' parameter acts as a switch to select the correct SQL query.
    if rating_type == 'final':
        sql = 'UPDATE teams SET final_rating = ?, final_rd = ?, final_vol = ? WHERE id = ?'
    else: # Default to updating the live leaderboard ratings
        sql = 'UPDATE teams SET rating = ?, rd = ?, vol = ? WHERE id = ?'

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(sql, (new_rating, new_rd, new_vol, team_id))
    conn.commit()
    conn.close()

def create_match(team0_id, team1_id):
    """Creates a new match record and returns its unique ID."""
    conn = get_db_connection()
    cur = conn.cursor()
    timestamp = datetime.datetime.now()
    # A match is considered 'active' by default when created
    cur.execute(
        'INSERT INTO matches (team_a_id, team_b_id, played_at) VALUES (?, ?, ?)',
        (team0_id, team1_id, timestamp)
    )
    match_id = cur.lastrowid # Get the ID of the row we just inserted
    conn.commit()
    conn.close()
    return match_id

def update_match_result(match_id, winner_code, replay_data):
    """Updates a match record with the final outcome."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'UPDATE matches SET winner_team_id = ?, replay_data = ? WHERE id = ?',
        (winner_code, replay_data, match_id)
    )
    conn.commit()
    conn.close()

# We will add more functions later for the leaderboard and submission process

def update_bot_path(team_id, bot_path):
    """
    Updates the active bot path for a given team.
    This is called after a successful new submission.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.datetime.now()

    cur.execute(
        'UPDATE teams SET active_bot_path = ?, last_submission = ? WHERE id = ?',
        (bot_path,now,team_id)
    )
    conn.commit()
    conn.close()
    print(f"✅ Updated active_bot_path for Team ID {team_id}.")

# Add these functions to server/database/db_handler.py

def get_playable_teams():
    """Fetches all teams that have a valid bot path."""
    conn = get_db_connection()
    teams = conn.execute(
        "SELECT id, name FROM teams WHERE active_bot_path IS NOT NULL AND active_bot_path != ''"
    ).fetchall()
    conn.close()
    return teams

def record_match(team_a_id, team_b_id, winner_id, round_number, replay_data):
    """Records a completed match in the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO matches (team_a_id, team_b_id, winner_team_id, tournament_round, replay_data, played_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (team_a_id, team_b_id, winner_id, round_number, replay_data, time.strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()

def count_completed_matches_for_round(round_number):
    """Counts how many matches have been completed for a given round."""
    conn = get_db_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM matches WHERE tournament_round = ?",
        (round_number,)
    ).fetchone()[0]
    conn.close()
    return count

def get_results_for_round(round_number):
    """Fetches all results for a given round to calculate scores."""
    conn = get_db_connection()
    results = conn.execute(
        "SELECT team_a_id, team_b_id, winner_team_id FROM matches WHERE tournament_round = ?",
        (round_number,)
    ).fetchall()
    conn.close()
    return results


def update_team_match_stats(team_a_id, team_b_id):
    """
    Updates the match stats for two teams after a game.
    Increments their match count and sets the current time as their last played time.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.datetime.now()
    
    # Update both teams in a single transaction
    cur.execute(
        "UPDATE teams SET matches_played = matches_played + 1, last_played_at = ? WHERE id = ?",
        (now, team_a_id)
    )
    cur.execute(
        "UPDATE teams SET matches_played = matches_played + 1, last_played_at = ? WHERE id = ?",
        (now, team_b_id)
    )
    
    conn.commit()
    conn.close()


def get_teams_for_matchmaking():
    """
    Fetches all playable teams, ordered by who is most "due" for a match.
    Teams that have never played are prioritized first, followed by those
    who haven't played in the longest time.
    """
    conn = get_db_connection()
    # The ORDER BY clause is key: NULLs (never played) come first,
    # then we sort by the oldest timestamp.
    teams = conn.execute(
        """
        SELECT
            id,
            name,
            final_rating AS rating,
            final_rd AS rd,
            matches_played
        FROM teams
        WHERE active_bot_path IS NOT NULL AND active_bot_path != ''
        ORDER BY rd DESC
        """
    ).fetchall()
    conn.close()
    # return teams
    # Also convert this to a dictionary if a team was found
    # Convert each sqlite3.Row object into a standard Python dictionary
    return [dict(row) for row in teams]

def have_teams_played_before(team_a_id, team_b_id):
    """Checks if two teams have a match record against each other."""
    conn = get_db_connection()
    # Check for both (A vs B) and (B vs A)
    count = conn.execute(
        """
        SELECT COUNT(*) FROM matches
        WHERE (team_a_id = ? AND team_b_id = ?) OR (team_a_id = ? AND team_b_id = ?)
        """,
        (team_a_id, team_b_id, team_b_id, team_a_id)
    ).fetchone()[0]
    conn.close()
    return count > 0

def get_replay_data(match_id):
    """
    Fetches the replay data JSON string for a single match from the database.
    """
    conn = get_db_connection()
    # Using row_factory allows us to access columns by name
    conn.row_factory = sqlite3.Row 
    
    result_row = conn.execute(
        "SELECT replay_data FROM matches WHERE id = ?",
        (match_id,)
    ).fetchone()
    
    conn.close()

    if result_row:
        return result_row['replay_data']
    else:
        # Return None if no match with that ID was found
        return None