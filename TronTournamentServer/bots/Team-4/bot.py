import sys
import json
import random

def main():
    # Loop over stdin to handle multiple turns
    for line in sys.stdin:
        try:
            # 1. Parse the Game State
            state = json.loads(line)
            
            width = state["board"]["width"]
            height = state["board"]["height"]
            grid = state["board"]["grid"]
            head = state["you"]["head"]
            
            possible_moves = ["UP", "DOWN", "LEFT", "RIGHT"]
            safe_moves = []

            # 2. Check each move to avoid walls/obstacles
            for move in possible_moves:
                hx, hy = head["x"], head["y"]
                if move == "UP": hy -= 1
                if move == "DOWN": hy += 1
                if move == "LEFT": hx -= 1
                if move == "RIGHT": hx += 1
                
                # Check bounds
                if not (0 <= hx < width and 0 <= hy < height):
                    continue
                
                # Check collisions (anything not '0' is dangerous)
                if grid[hy][hx] != '0':
                    continue
                
                safe_moves.append(move)

            # 3. Choose move
            if safe_moves:
                chosen_move = random.choice(safe_moves)
            else:
                chosen_move = random.choice(possible_moves)

            # 4. Send JSON response (CRITICAL FIX)
            response = {"move": chosen_move}
            print(json.dumps(response))
            sys.stdout.flush()
            
        except Exception as e:
            # If anything breaks, output a random fallback so we don't crash the engine
            # Write error to stderr so we can see it in logs, but keep playing
            sys.stderr.write(str(e))
            print(json.dumps({"move": "UP"}))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
