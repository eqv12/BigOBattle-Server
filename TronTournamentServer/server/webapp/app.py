# server/webapp/app.py

import datetime
import os
import shutil
from server import config
import zipfile
import uuid
from server.logic import engine
import json
from flask import Flask, request, jsonify # type: ignore


# --- Project-specific imports ---
# These imports assume you run this from the project root with `python -m server.webapp.app`
from server import config
from server.database import db_handler

# 1. Initialize the Flask Application
app = Flask(__name__)

# --- Placeholder Authentication ---
# In a real application, this would check a browser session or an API token.
# For now, we'll just hardcode it to always return the same team name for testing.
def get_authenticated_team_name():
    """
    A placeholder function for user authentication.
    TODO: Replace this with a real login system later.
    """
    return "Team-2" # Assume the user is always Team-1 for now

# --- Web Routes (API Endpoints) ---

@app.route('/')
def index():
    """A simple homepage to confirm the server is running."""
    return "<h1>Tron Tournament Server is Online!</h1>"

# In server/webapp/app.py, REPLACE your handle_bot_submission function with this:

# In server/webapp/app.py, REPLACE your handle_bot_submission function with this:

@app.route('/submit', methods=['POST'])
def handle_bot_submission():
    """Handles the zipped bot file submission with direct authentication."""
    
    # 1. Get credentials and file from the form submission.
    if 'team_name' not in request.form:
        return jsonify({"error": "Missing team_name in form data"}), 400
    
    team_name = request.form['team_name']


    # --- ADD THIS NEW BLOCK FOR RATE LIMITING ---
    team = db_handler.get_team_by_name(team_name)
    if team and team['last_submission']:
        # Convert the string from the DB back into a datetime object
        last_sub_time = datetime.datetime.strptime(team['last_submission'], '%Y-%m-%d %H:%M:%S.%f')
        time_since_last_sub = datetime.datetime.now() - last_sub_time
        
        limit_seconds = config.SUBMISSION_RATE_LIMIT_MINUTES * 60
        if time_since_last_sub.total_seconds() < limit_seconds:
            wait_time = limit_seconds - time_since_last_sub.total_seconds()
            return jsonify({"error": f"Rate limit exceeded. Please wait {int(wait_time)} more seconds."}), 429 # "Too Many Requests"

    # --- END OF NEW BLOCK ---

    # ... (the rest of the function continues as normal) ...


    if not config.ALLOW_PASSWORDLESS_SUBMISSIONS:
        if 'password' not in request.form:
            return jsonify({"error": "Missing password in form data"}), 400
        password = request.form['password']
        if not db_handler.verify_team_credentials(team_name, password):
            return jsonify({"error": "Authentication failed: Invalid credentials"}), 401
    
                
    # 2. Authenticate the user against the database.
    # if not db_handler.verify_team_credentials(team_name, password):
    #     return jsonify({"error": "Authentication failed: Invalid credentials"}), 401

    # 3. Check if a file was included in the request.
    if 'bot_zip_file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['bot_zip_file']
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    # 4. Define the final destination path and clean it out.
    destination_path = os.path.join(config.BOTS_DIR, team_name)
    if os.path.exists(destination_path):
        shutil.rmtree(destination_path)
    os.makedirs(destination_path)

    # --- NEW LOGIC STARTS HERE ---

    # 5. Create a temporary directory for extraction.
    temp_extract_path = os.path.join(destination_path, "temp_extraction")
    os.makedirs(temp_extract_path)

    try:
        # 6. Extract the zip file into the temporary directory.
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_path)

        # 7. Find the created subfolder and move its contents to the destination.
        extracted_items = os.listdir(temp_extract_path)
        
        # Check if the zip contained a single root folder.
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_extract_path, extracted_items[0])):
            unzipped_root_folder = os.path.join(temp_extract_path, extracted_items[0])
            # Move each item from the subfolder to the destination
            for item in os.listdir(unzipped_root_folder):
                shutil.move(os.path.join(unzipped_root_folder, item), destination_path)
        else:
            # If no single root folder, move all extracted items directly.
            for item in extracted_items:
                shutil.move(os.path.join(temp_extract_path, item), destination_path)

    except zipfile.BadZipFile:
        return jsonify({"error": "Invalid file format. Please upload a ZIP file."}), 400
    finally:
        # 8. Clean up the temporary directory.
        if os.path.exists(temp_extract_path):
            shutil.rmtree(temp_extract_path)
    
    # --- NEW LOGIC ENDS HERE ---

    # 9. Update the database.
    team = db_handler.get_team_by_name(team_name)
    if team:
        # run_script_path = os.path.join(destination_path, 'run.sh')
        run_script_path = os.path.join(destination_path, 'run.sh').replace('\\', '/')
        db_handler.update_bot_path(team['id'], run_script_path)

        #resets the stats for new submission
        db_handler.reset_team_stats_for_recalibration(team['id'])

    
    return jsonify({"message": f"Bot for {team_name} uploaded successfully!"}), 200

# In server/webapp/app.py

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """
    Returns the top rated teams for the live dashboard.
    """
    # 1. Fetch all teams from the database
    all_teams = db_handler.get_all_teams()
    
    # 2. Sort them by Rating (Descending)
    sorted_teams = sorted(all_teams, key=lambda x: x['rating'], reverse=True)
    
    # 3. Format the data for the frontend
    leaderboard_data = []
    for rank, team in enumerate(sorted_teams, 1):
        # Calculate a simple Win Rate for display
        wins = team.get('wins', 0)
        losses = team.get('losses', 0)
        draws = team.get('draws', 0)
        total_games = wins + losses + draws
        win_rate = 0.0
        if total_games > 0:
            win_rate = round((wins / total_games) * 100, 1)

        leaderboard_data.append({
            "rank": rank,
            "team_name": team['name'],
            "rating": int(team['rating']),
            "matches_played": total_games,
            "win_rate": f"{win_rate}%",
            "rd": int(team['rd'])
        })
    
    # Return top 50 only to keep it light
    return jsonify(leaderboard_data[:50])

# In server/webapp/app.py

@app.route('/test', methods=['POST'])
def handle_test_match():
    """
    Runs a quick, unranked match between the uploaded code and a CPU bot.
    Returns the GameState.json immediately.
    """
    # 1. Basic Validation
    if 'bot_zip_file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    opponent_type = request.form.get('opponent', 'random') # Default to random
    file = request.files['bot_zip_file']
    
    # 2. Create a temporary isolation chamber for this test
    # We use a UUID so multiple people can test at once without overwriting
    test_id = str(uuid.uuid4())
    test_dir = os.path.join(config.BOTS_DIR, f"test_{test_id}")
    os.makedirs(test_dir)

    try:
        # 3. Unzip the User's Bot
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(test_dir)
        
        # Identify the user's run file
        # (This is a simplified check; in prod we'd look for run.sh recursively)
        user_bot_path = os.path.join(test_dir, "run.sh").replace('\\', '/')
        if not os.path.exists(user_bot_path):
             # Try to find it if it's in a subfolder
             for root, dirs, files in os.walk(test_dir):
                 if "run.sh" in files:
                     user_bot_path = os.path.join(root, "run.sh").replace('\\', '/')
                     break

        # 4. Select the Opponent
        # We point to the local copies of the starter bots on the server
        opponent_map = {
            "random": "bots/random_bot/run.sh",
            "greedy": "bots/space_filler_bot/run.sh", # Assuming you have this
            "self": user_bot_path # Play against yourself
        }
        
        opponent_path = opponent_map.get(opponent_type)
        if not opponent_path or (opponent_type != 'self' and not os.path.exists(opponent_path)):
             # Fallback to random if the requested bot is missing
             opponent_path = "bots/random_bot/run.sh"

        # 5. Run the Engine DIRECTLY (Bypass the Queue)
        # We pass the paths directly to the engine
        match_result = engine.run_match(user_bot_path, opponent_path)
        
        # 6. Return the Replay Data
        # The frontend will use this to render the match
        return jsonify({
            "status": "success",
            "winner": match_result['winner'],
            "replay": json.loads(match_result['replay']), # Parse string to JSON object
            "termination": match_result['termination_reason']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    finally:
        # 7. Cleanup: Delete the temp folder
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


# --- This block allows you to run the server directly ---
if __name__ == '__main__':
    # debug=True allows the server to auto-reload when you save changes.
    # host='0.0.0.0' makes the server accessible from other computers on your network.
    app.run(host='0.0.0.0', port=5000, debug=True)