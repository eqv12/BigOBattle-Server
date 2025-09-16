# This is the main entry point to start the entire tournament server.
# It orchestrates the startup of the background matchmaker and the foreground web app.

import multiprocessing
import os
import sys

# This boilerplate ensures the script can find our other server modules
# when run from the project's root directory.
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Import our custom modules
from server.logic import matchmaker
from server.webapp.app import create_app
from server.database.setup_database import setup_database

if __name__ == '__main__':
    # This ensures that multiprocessing works correctly, especially on Windows
    multiprocessing.freeze_support()

    print("--- TRON TOURNAMENT SERVER ---")
    
    # --- 1. Setup the Database ---
    # This will create the DB and generate teams if it's the first run.
    # If the DB already exists, it will do nothing.
    print("Checking database...")
    setup_database()
    
    # --- 2. Start the Matchmaker in the Background ---
    # The start_matchmaker() function from our module creates the worker pool
    # and returns the shared queue that the web app needs to use.
    print("Starting background matchmaker process...")
    match_queue = matchmaker.start_matchmaker()
    
    # --- 3. Create and Start the Flask Web App ---
    # We pass the shared match_queue into the Flask app factory.
    # This gives the web app a way to send "orders" to the "kitchen".
    print("Creating Flask web application...")
    app = create_app(match_queue)
    
    # --- 4. Run the Web Server ---
    # This is a blocking call. The server will run here and handle web requests
    # until you stop the script (e.g., with Ctrl+C).
    print("🚀 Server is running on http://0.0.0.0:5000")
    print("Press Ctrl+C to stop the server.")
    app.run(host='0.0.0.0', port=5000)
