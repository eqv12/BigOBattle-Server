#!/bin/bash
echo "--- Starting Tron Tournament Server ---"

# Check if dependencies are installed
if ! python -c "import flask, glicko2" &> /dev/null; then
    echo "⚠️  Dependencies not found. Installing from server/requirements.txt..."
    pip install -r server/requirements.txt
fi

echo "Starting Flask Web App on http://0.0.0.0:5000"
# export FLASK_APP=server/webapp/app.py
export FLASK_APP=server.webapp.app
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
