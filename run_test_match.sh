#!/bin/bash

# This script is the DEBUGGING VERSION. Its primary goal is to capture
# any and all error messages from the Python engine process to diagnose
# the silent failure.

# --- Configuration ---
PROJECT_DIR="TronTournamentServer"
BOT_A_PATH="bots_official/Team_Alpha"
BOT_B_PATH="bots_official/Team_Beta"
ENGINE_MODULE="server.logic.engine"
VISUALIZER_SCRIPT="../visualizer.py"
MATCH_ID=999
ENGINE_LOG_FILE="engine_errors.log"

# --- 1. SETUP: Create the dummy bots ---
echo "⚙️  Setting up dummy bots in '$PROJECT_DIR/bots_official'..."
# (Setup part is unchanged and correct)
read -r -d '' BOT_PYTHON_CODE << EOM
import sys, json, random
def decide_move(gs):
    my_head = gs['you']['head']
    grid = gs['board']['grid']
    moves = {"UP": [0, -1], "DOWN": [0, 1], "LEFT": [-1, 0], "RIGHT": [1, 0]}
    possible = []
    for m, (dx, dy) in moves.items():
        nx, ny = my_head['x'] + dx, my_head['y'] + dy
        if 0 <= nx < 25 and 0 <= ny < 25 and grid[ny][nx] == '.':
            possible.append(m)
    if not possible: return "UP"
    return random.choice(possible)
if __name__ == "__main__":
    while True:
        line = sys.stdin.readline()
        if not line: break
        try:
            gs = json.loads(line)
            move = decide_move(gs)
            print(json.dumps({"move": move}), flush=True)
        except:
            print(json.dumps({"move": "UP"}), flush=True)
EOM
read -r -d '' BOT_RUN_SCRIPT << EOM
#!/bin/bash
python3 bot.py
EOM
mkdir -p "$PROJECT_DIR/$BOT_A_PATH"
mkdir -p "$PROJECT_DIR/$BOT_B_PATH"
echo "$BOT_PYTHON_CODE" > "$PROJECT_DIR/$BOT_A_PATH/bot.py"
echo "$BOT_RUN_SCRIPT" > "$PROJECT_DIR/$BOT_A_PATH/run.sh"
chmod +x "$PROJECT_DIR/$BOT_A_PATH/run.sh"
echo "$BOT_PYTHON_CODE" > "$PROJECT_DIR/$BOT_B_PATH/bot.py"
echo "$BOT_RUN_SCRIPT" > "$PROJECT_DIR/$BOT_B_PATH/run.sh"
chmod +x "$PROJECT_DIR/$BOT_B_PATH/run.sh"
echo "✅ Bots are ready."
echo ""

# --- 2. EXECUTION: Change directory and run the engine with full error logging ---
echo "⚔️  Running a single match from within '$PROJECT_DIR'..."
cd "$PROJECT_DIR" || exit

echo "--- DEBUG INFO ---"
echo "Current Directory: $(pwd)"
echo "Python executable being used: $(which py)"
echo "--------------------"

# --- KEY CHANGE: Capture all output and check the exit code ---
# We redirect stdout and stderr to a log file to capture EVERYTHING.
py -u -m $ENGINE_MODULE $BOT_A_PATH $BOT_B_PATH $MATCH_ID > $ENGINE_LOG_FILE 2>&1
EXIT_CODE=$? # Capture the exit code of the last command

# --- 3. ANALYSIS: Check if the engine ran successfully ---
REPLAY_FILE="replays/${MATCH_ID}.json"
echo ""

if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ FATAL ERROR: The Python engine process crashed!"
    echo "   Exit Code: $EXIT_CODE"
    echo "   The error message has been captured in: '$PROJECT_DIR/$ENGINE_LOG_FILE'"
    echo "   --- ERROR LOG CONTENTS ---"
    cat $ENGINE_LOG_FILE
    echo "   ------------------------"
    exit 1
fi

if [ -f "$REPLAY_FILE" ]; then
    echo "🎬 Match complete. Launching visualizer for '$REPLAY_FILE'..."
    py $VISUALIZER_SCRIPT $REPLAY_FILE
    echo "✅ Test finished."
else
    echo "❌ Error: Engine ran without crashing but did not produce a replay file."
    echo "   Check the contents of '$PROJECT_DIR/$ENGINE_LOG_FILE' for clues."
    exit 1
fi
```

### What To Do Now

1.  Replace the contents of `run_test_match.sh` with this new **debugging version**.
2.  Run the script again from your `D:\Login_25\BigOBattle\bob2` directory.

```bash
./run_test_match.sh

