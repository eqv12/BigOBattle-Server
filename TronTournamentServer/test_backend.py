import requests
import zipfile
import io
import os
import json

# Configuration
SERVER_URL = "http://127.0.0.1:5000"
TEAM_NAME = "Arch-Tester-Bot"
PASSWORD = "password123"

def create_dummy_bot_zip():
    """Creates a valid zip file in memory containing a simple Python bot."""
    print("📦 Creating in-memory dummy bot...")
    
    # A simple bot that just moves 'UP'
    bot_code = """
import sys
while True:
    line = sys.stdin.readline()
    if not line: break
    print("UP")
    sys.stdout.flush()
"""
    run_script = "python3 bot.py"
    
    # Create zip in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("bot.py", bot_code)
        zip_file.writestr("run.sh", run_script)
    
    zip_buffer.seek(0)
    return zip_buffer

def test_leaderboard():
    print(f"\n--- 1. Testing GET {SERVER_URL}/leaderboard ---")
    try:
        response = requests.get(f"{SERVER_URL}/leaderboard")
        if response.status_code == 200:
            print("✅ Leaderboard accessible!")
            print(f"   Response: {json.dumps(response.json()[:2], indent=2)}") # Show top 2 only
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_submit(zip_obj):
    print(f"\n--- 2. Testing POST {SERVER_URL}/submit ---")
    files = {'bot_zip_file': ('bot.zip', zip_obj, 'application/zip')}
    data = {'team_name': TEAM_NAME, 'password': PASSWORD}
    
    try:
        # We need to reset the file pointer because we might have read it before
        zip_obj.seek(0)
        response = requests.post(f"{SERVER_URL}/submit", files=files, data=data)
        
        if response.status_code == 200:
            print("✅ Submission Successful!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_match(zip_obj):
    print(f"\n--- 3. Testing POST {SERVER_URL}/test (Debug Match) ---")
    files = {'bot_zip_file': ('bot.zip', zip_obj, 'application/zip')}
    data = {'opponent': 'random'} # Play against random bot
    
    try:
        zip_obj.seek(0)
        response = requests.post(f"{SERVER_URL}/test", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test Match Completed!")
            print(f"   Winner: {result.get('winner')}")
            print(f"   Replay Data Size: {len(str(result.get('replay')))} chars")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    # Ensure server is running
    print(f"🚀 Connecting to Backend at {SERVER_URL}...")
    
    # Generate the payload once
    dummy_zip = create_dummy_bot_zip()
    
    # Run tests
    test_leaderboard()
    test_submit(dummy_zip)
    test_match(dummy_zip)
    print("\n✅ DONE. If all green, your Backend is perfect.")