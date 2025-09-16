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
