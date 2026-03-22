import os
import shutil
import sqlite3
from datetime import datetime

from server.config import DATABASE_FILE

MIGRATION_FILE = os.path.join(os.path.dirname(__file__), "migrations", "20260321_room_schema.sql")


def backup_database(db_path: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def run_migration() -> None:
    if not os.path.exists(DATABASE_FILE):
        raise FileNotFoundError(f"Database file not found: {DATABASE_FILE}")

    if not os.path.exists(MIGRATION_FILE):
        raise FileNotFoundError(f"Migration file not found: {MIGRATION_FILE}")

    backup_path = backup_database(DATABASE_FILE)
    print(f"✅ Backup created: {backup_path}")

    with open(MIGRATION_FILE, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = sqlite3.connect(DATABASE_FILE)
    try:
        conn.executescript(sql)
        conn.commit()
        print("✅ Room schema migration complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
