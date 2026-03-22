-- Room-first schema migration
-- Date: 2026-03-21

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL UNIQUE,
    admin_password_hash TEXT NOT NULL,
    game_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT,
    active_bot_path TEXT,
    created_at DATETIME NOT NULL,
    last_submission_at DATETIME,
    FOREIGN KEY(room_id) REFERENCES rooms(id),
    UNIQUE(room_id, display_name)
);

CREATE TABLE IF NOT EXISTS room_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    rating REAL NOT NULL DEFAULT 1500.0,
    rd REAL NOT NULL DEFAULT 350.0,
    vol REAL NOT NULL DEFAULT 0.06,
    matches_played INTEGER NOT NULL DEFAULT 0,
    last_played_at DATETIME,
    FOREIGN KEY(room_id) REFERENCES rooms(id),
    FOREIGN KEY(participant_id) REFERENCES participants(id),
    UNIQUE(room_id, participant_id)
);

CREATE TABLE IF NOT EXISTS room_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    game_key TEXT NOT NULL,
    participant_a_id INTEGER NOT NULL,
    participant_b_id INTEGER NOT NULL,
    winner_participant_id INTEGER,
    replay_data TEXT,
    termination_reason TEXT,
    played_at DATETIME NOT NULL,
    FOREIGN KEY(room_id) REFERENCES rooms(id),
    FOREIGN KEY(participant_a_id) REFERENCES participants(id),
    FOREIGN KEY(participant_b_id) REFERENCES participants(id),
    FOREIGN KEY(winner_participant_id) REFERENCES participants(id)
);
