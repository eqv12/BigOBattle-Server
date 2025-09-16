#!/bin/bash

# This script generates the server application structure and configures it
# to use a pre-existing Docker Hub image, skipping the local build process.

# --- 1. Create the main project directory ---
echo "🚀 Creating main project folder: TronTournamentServer/"
mkdir -p TronTournamentServer
cd TronTournamentServer

# --- 2. Create the Server-Side Infrastructure ---
echo "🏗️  Setting up server-side folders and files..."
mkdir -p server/webapp/templates
mkdir -p server/webapp/static
mkdir -p server/logic
mkdir -p server/database
mkdir -p bots_official

touch server/webapp/app.py
touch server/webapp/static/style.css
touch server/webapp/static/script.js
touch server/webapp/templates/index.html
touch server/database/db_handler.py
touch server/logic/rating_system.py
touch server/logic/matchmaker.py
touch server/logic/engine.py
touch server/logic/game_state.py

echo "✅ Server-side file structure created."

# --- 3. Create the Root-Level Configuration Files ---
echo "🔧 Creating root-level configuration for the server..."

# NEW: Create a central config.py instead of a Dockerfile
echo "⚙️  Creating central config.py with your Docker Hub image..."
cat > server/config.py <<- EOM
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
WORKER_PROCESSES = 8

# --- Engine Configuration ---
MOVE_TIMEOUT_S = 0.1
MEMORY_LIMIT_MB = 256
EOM

# Server requirements.txt
cat > server/requirements.txt <<- EOM
Flask
glicko2
EOM

# Main server runner script
cat > run_server.sh <<- EOM
#!/bin/bash
echo "--- Starting Tron Tournament Server ---"

# Check if dependencies are installed
if ! python -c "import flask, glicko2" &> /dev/null; then
    echo "⚠️  Dependencies not found. Installing from server/requirements.txt..."
    pip install -r server/requirements.txt
fi

echo "Starting Flask Web App on http://0.0.0.0:5000"
export FLASK_APP=server/webapp/app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
EOM

# Make the server runner script executable
chmod +x run_server.sh

echo ""
echo "✅ Project 'TronTournamentServer' created successfully!"
echo "⚠️  Dockerfile creation was SKIPPED as requested."
echo ""
echo "Navigate into the directory with: cd TronTournamentServer"
echo ""
echo "Your new setup workflow is:"
echo "  1. Pull the Docker image from the Hub: docker pull ramyar1206/tron-battle-env"
echo "  2. Install server dependencies: pip install -r server/requirements.txt"
echo "  3. Start the server: ./run_server.sh"

