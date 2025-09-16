import sys, json, random

def decide_move(gs):
    my_head = gs['you']['head']
    grid = gs['board']['grid']
    width = gs['board']['width']
    height = gs['board']['height']

    moves = {"UP": [0, -1], "DOWN": [0, 1], "LEFT": [-1, 0], "RIGHT": [1, 0]}
    possible = []

    for move, (dx, dy) in moves.items():
        nx, ny = my_head['x'] + dx, my_head['y'] + dy

        # Check if the new position is within bounds and is an empty space ('0')
        if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == '0':
            possible.append(move)
    
    # If there are no safe moves, default to moving UP (and likely losing)
    if not possible:
        return "UP"
    
    # Otherwise, choose a random valid move
    return random.choice(possible)

if __name__ == "__main__":
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        
        try:
            game_state = json.loads(line)
            move = decide_move(game_state)
            # The flush=True is critical to prevent the buffering issue
            print(json.dumps({"move": move}), flush=True)
        except Exception:
            # If any error occurs, default to moving UP as a failsafe
            print(json.dumps({"move": "UP"}), flush=True)