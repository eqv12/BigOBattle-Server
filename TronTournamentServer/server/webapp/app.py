# server/webapp/app.py

import datetime
import os
import shutil
from server import config
import zipfile
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

# --- This block allows you to run the server directly ---
if __name__ == '__main__':
    # debug=True allows the server to auto-reload when you save changes.
    # host='0.0.0.0' makes the server accessible from other computers on your network.
    app.run(host='0.0.0.0', port=5000, debug=True)