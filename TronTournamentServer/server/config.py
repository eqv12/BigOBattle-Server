# This file holds all important configuration variables for the server.
# It's the single source of truth for settings.

# --- Docker Configuration ---
# The full name of the pre-built image on Docker Hub.
# To update the image later, you only need to change this one line.

# DOCKER_IMAGE_NAME = "ramyar1206/tron-battle-env:latest"
#command to run docker is docker build -t tron-final-env .   ----with the . please
DOCKER_IMAGE_NAME = "tron-local-env"


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
ROOM_BOTS_DIR = "bots_submissions"

#in case stuff needs time to startup
FIRST_MOVE_TIMEOUT_S = 3.0

# The number of matches a new bot submission should play to get an
# initial, more accurate rating.
CALIBRATION_MATCHES = 3

# The range (+/-) within which the matchmaker will pair opponents.
MATCHMAKING_RATING_WINDOW = 200

DEFAULT_RD = 350.0

ALLOW_PASSWORDLESS_SUBMISSIONS = True

# For the live matchmaker, run this many calibration ticks for every 1 general tick.
MATCHMAKING_RATIO = 3


#do a full reset for new submission or only rd and matches
reset_full=True

SUBMISSION_RATE_LIMIT_MINUTES = 2
