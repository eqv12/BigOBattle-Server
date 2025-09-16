# This file holds all important configuration variables for the server.
# It's the single source of truth for settings.

# --- Docker Configuration ---
# The full name of the pre-built image on Docker Hub.
# To update the image later, you only need to change this one line.
DOCKER_IMAGE_NAME = "ramyar1206/tron-battle-env:latest"

# --- Game Configuration ---
GRID_WIDTH = 25
GRID_HEIGHT = 25
MAX_TURNS = 500

# --- Matchmaker Configuration ---
# Set to the number of CPU cores to use for running matches.
WORKER_PROCESSES = 4

# --- Engine Configuration ---
MOVE_TIMEOUT_S = 0.5
MEMORY_LIMIT_MB = 256
DATABASE_FILE = "server/database/tournament.db"
BOTS_DIR ="bots_official"