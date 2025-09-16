import sqlite3
import hashlib
import secrets
import os
import json # <-- Added for JSON output

# --- Configuration ---
DB_FOLDER = "D:\Login_25\BigOBattle\bob2\TronTournamentServer\server\database"
DATABASE_FILE = os.path.join(DB_FOLDER, "tournament.db")
TEAMS_TO_GENERATE = 5
PASSWORD_LIST_FILE_TXT = "organizer_passwords.txt" # For human-readable output
PASSWORD_LIST_FILE_JSON = "organizer_passwords.json" # For machine-readable output

def hash_password(password):
    """Hashes a password using SHA-256 for secure storage."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def setup_database():
    """
    Creates and initializes the database. This is a one-time setup script.
    - Creates the necessary tables if they don't exist.
    - Populates the 'teams' table with a predefined number of teams.
    - Generates a master password list for the organizers in both TXT and JSON formats.
    """
    os.makedirs(DB_FOLDER, exist_ok=True)
    print(f"Setting up database at '{DATABASE_FILE}'...")
    con = sqlite3.connect(DATABASE_FILE)
    cur = con.cursor()

    # --- Create the 'teams' table ---
    cur.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            rating REAL NOT NULL,
            rd REAL NOT NULL,
            vol REAL NOT NULL,
            active_bot_path TEXT,
            last_submission DATETIME
        )
    ''')

    # --- Create the 'matches' table ---
    cur.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team0_id INTEGER,
            team1_id INTEGER,
            winner_id INTEGER,
            replay_filename TEXT,
            played_at DATETIME,
            is_active BOOLEAN,
            FOREIGN KEY(team0_id) REFERENCES teams(id),
            FOREIGN KEY(team1_id) REFERENCES teams(id)
        )
    ''')

    # --- Check if teams are already generated ---
    cur.execute("SELECT COUNT(*) FROM teams")
    if cur.fetchone()[0] > 0:
        print("✅ Database and tables already exist. Teams are already generated.")
        con.close()
        return

    # --- Generate Teams and Passwords ---
    print(f"Generating {TEAMS_TO_GENERATE} teams and a password list...")
    passwords_for_txt = []
    passwords_for_json = [] # <-- New list to hold data for JSON
    
    # Default Glicko-2 values for new players
    default_rating = 1500.0
    default_rd = 350.0
    default_vol = 0.06

    for i in range(1, TEAMS_TO_GENERATE + 1):
        team_name = f"Team-{i}"
        password = secrets.token_hex(8) # Generate a secure, 16-character random password
        password_hash = hash_password(password)
        
        # Store credentials for both file formats
        passwords_for_txt.append(f"Name: {team_name}, Password: {password}")
        passwords_for_json.append({"name": team_name, "password": password}) # <-- Add to JSON list

        # Insert the team with its hashed password into the database
        cur.execute(
            "INSERT INTO teams (name, password_hash, rating, rd, vol) VALUES (?, ?, ?, ?, ?)",
            (team_name, password_hash, default_rating, default_rd, default_vol)
        )

    # --- Save the master password lists to files ---
    with open(PASSWORD_LIST_FILE_TXT, "w") as f:
        f.write("\n".join(passwords_for_txt))
    print(f"✅ Human-readable password list saved to '{PASSWORD_LIST_FILE_TXT}'.")

    # --- NEW: Save the JSON file ---
    with open(PASSWORD_LIST_FILE_JSON, "w") as f:
        json.dump(passwords_for_json, f, indent=2)
    print(f"✅ Machine-readable password list saved to '{PASSWORD_LIST_FILE_JSON}'.")
    print("KEEP THESE FILES SAFE.")
    
    con.commit()
    con.close()
    print("✅ Database setup complete.")

if __name__ == "__main__":
    setup_database()

