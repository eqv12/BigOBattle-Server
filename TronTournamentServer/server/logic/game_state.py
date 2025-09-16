import sys
import os
import json
from collections import deque

# --- BOILERPLATE TO MAKE SCRIPT RUNNABLE ---
# This block of code adds the project's root directory to the Python path.
# This makes the absolute imports (like 'from server.config...') work
# even when the script is executed directly.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
# -------------------------------------------

from server.config import GRID_WIDTH, GRID_HEIGHT

class Player:
    """Represents a single player in the game."""
    def __init__(self, player_id, start_x, start_y):
        self.id = player_id
        self.path = [(start_x, start_y)]
        self.is_alive = True
    @property
    def head(self):
        """Returns the current head position of the player's trail."""
        return self.path[-1]

class GameState:
    """Represents the entire state of the game board and handles game logic."""
    def __init__(self, players):
        self.players = players
        self.grid = [[-1 for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
        for p in self.players:
            if p.is_alive:
                self.grid[p.head[0]][p.head[1]] = p.id

    def update_player_move(self, player_id, move):
        """Validates a player's move and updates the game state."""
        player = self.players[player_id]
        if not player.is_alive: return

        head_x, head_y = player.head
        new_head = (head_x, head_y)
        if move == "UP": new_head = (head_x, head_y - 1)
        elif move == "DOWN": new_head = (head_x, head_y + 1)
        elif move == "LEFT": new_head = (head_x - 1, head_y)
        elif move == "RIGHT": new_head = (head_x + 1, head_y)
        else:
            player.is_alive = False
            return
            
        nx, ny = new_head
        if not (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT) or self.grid[nx][ny] != -1:
            player.is_alive = False
        else:
            player.path.append(new_head)
            self.grid[nx][ny] = player.id

    def count_territory(self, player_id):
        """Calculates the number of empty, reachable squares for a player (BFS)."""
        player = self.players[player_id]
        if not player.is_alive: return 0
        q = deque([player.head])
        visited = {player.head}
        count = 0
        while q:
            x, y = q.popleft()
            count += 1
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and
                        self.grid[nx][ny] == -1 and (nx, ny) not in visited):
                    visited.add((nx, ny))
                    q.append((nx, ny))
        return count - len(player.path)

    def to_json_for_player(self, player_id, turn):
        """Serializes the game state to the rich JSON format for a bot."""
        you = self.players[player_id]
        opponent = self.players[1 - player_id]
        
        grid_str_array = []
        for y in range(GRID_HEIGHT):
            row_str = ""
            for x in range(GRID_WIDTH):
                cell = self.grid[x][y]
                if cell == -1: row_str += "."
                elif cell == you.id: row_str += "0"
                else: row_str += "1"
            grid_str_array.append(row_str)

        state_representation = {
            "turn": turn,
            "board": {"height": GRID_HEIGHT, "width": GRID_WIDTH, "grid": grid_str_array},
            "you": {
                "id": f"p{you.id}", "head": {"x": you.head[0], "y": you.head[1]},
                "body": [{"x": px, "y": py} for px, py in reversed(you.path)], "length": len(you.path)
            },
            "opponent": {
                "id": f"p{opponent.id}", "head": {"x": opponent.head[0], "y": opponent.head[1]},
                "body": [{"x": px, "y": py} for px, py in reversed(opponent.path)], "length": len(opponent.path)
            }
        }
        return json.dumps(state_representation) + '\n'

    def get_log_data(self, winner_id):
        """Creates the dictionary for the JSON replay file."""
        return {
            "grid_size": (GRID_WIDTH, GRID_HEIGHT), "winner_id": winner_id,
            "players": [{"id": p.id, "path": p.path} for p in self.players]
        }

