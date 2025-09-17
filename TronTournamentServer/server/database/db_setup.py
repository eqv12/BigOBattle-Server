import sqlite3
import hashlib
import secrets
import os
import json
import random

# --- Configuration ---
from server.config import DATABASE_FILE
TEAMS_TO_GENERATE = 25 # Increased for a full tournament
PASSWORD_LIST_FILE_TXT = "organizer_passwords.txt"
PASSWORD_LIST_FILE_JSON = "organizer_passwords.json"

PASSWORDSS = [
    "marshmallow", "flippers", "waffles", "scooter", "popsicle",
    "jellybean", "cupcake", "snorkel", "hedgehog", "toaster",
    "lollipop", "otter", "sundae", "gummybear", "puzzle",
    "pancakes", "sprinkles", "koala", "kazoo", "pickles",
    "bubbles", "slippers", "squidgy", "cheesecake", "yoyo",
    "noodles", "unicorn", "cabbage", "platypus", "banjo",
    "cloudberry", "iguana", "muffin", "raccoon", "trombone",
    "jellyfish", "pebbles", "nachos", "biscuit", "velcro",
    "wafflestomp", "doodle", "pogo", "scoops", "zebra",
    "mango", "churro", "walrus", "bubblegum", "taco"
]


def hash_password(password):
    """Hashes a password using SHA-256 for secure storage."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def setup_database():
    """
    Creates and initializes the database with the updated schema.
    """
    # os.makedirs(DB_FOLDER, exist_ok=True)
    print(f"Setting up database at '{DATABASE_FILE}'...")
    con = sqlite3.connect(DATABASE_FILE)
    cur = con.cursor()

    # --- Create the 'teams' table (UPDATED SCHEMA) ---
    cur.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new', -- 'new', 'verified', or 'error'
            active_bot_path TEXT,
            last_submission DATETIME,

            -- Glicko-2 ratings for the LIVE LEADERBOARD
            rating REAL NOT NULL,
            rd REAL NOT NULL,
            vol REAL NOT NULL,

            -- Glicko-2 ratings for the FINAL TOURNAMENT
            final_rating REAL NOT NULL,
            final_rd REAL NOT NULL,
            final_vol REAL NOT NULL
        )
    ''')

    # --- Create the 'matches' table (Using recommended schema) ---
    cur.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_a_id INTEGER,
            team_b_id INTEGER,
            winner_team_id INTEGER, -- Stores the actual team ID of the winner, or NULL for a draw
            replay_data TEXT,
            played_at DATETIME,
            tournament_round INTEGER, -- Essential for Swiss tournament logic
            FOREIGN KEY(team_a_id) REFERENCES teams(id),
            FOREIGN KEY(team_b_id) REFERENCES teams(id)
        )
    ''')
    
    # --- Check if teams are already generated ---
    cur.execute("SELECT COUNT(*) FROM teams")
    if cur.fetchone()[0] > 0:
        print("✅ Database and tables already exist. Teams are already generated.")
        con.close()
        return

    # --- Generate Teams and Passwords ---
    print(f"Generating {TEAMS_TO_GENERATE} teams...")
    passwords_for_txt = []
    passwords_for_json = []
    
    # Default Glicko-2 starting values
    default_rating = 1500.0
    default_rd = 350.0
    default_vol = 0.06


    random.shuffle(PASSWORDSS)

    for i in range(1, TEAMS_TO_GENERATE + 1):
        team_name = f"Team-{i}"
        # password = secrets.token_hex(8)
        password = PASSWORDSS[i - 1]
        password_hash = hash_password(password)
        
        passwords_for_txt.append(f"Name: {team_name}, Password: {password}")
        passwords_for_json.append({"name": team_name, "password": password})

        # Insert a new team, initializing BOTH sets of Glicko-2 ratings
        cur.execute(
            """
            INSERT INTO teams (
                name, password_hash, 
                rating, rd, vol, 
                final_rating, final_rd, final_vol
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                team_name, password_hash,
                default_rating, default_rd, default_vol,
                default_rating, default_rd, default_vol
            )
        )

    # --- Save the master password lists to files ---
    with open(PASSWORD_LIST_FILE_TXT, "w") as f:
        f.write("\n".join(passwords_for_txt))
    print(f"✅ Human-readable password list saved to '{PASSWORD_LIST_FILE_TXT}'.")

    with open(PASSWORD_LIST_FILE_JSON, "w") as f:
        json.dump(passwords_for_json, f, indent=2)
    print(f"✅ Machine-readable password list saved to '{PASSWORD_LIST_FILE_JSON}'.")
    
    con.commit()
    con.close()
    print("✅ Database setup complete.")

if __name__ == "__main__":
    # If you run this script directly, it will create/update the database.
    setup_database()