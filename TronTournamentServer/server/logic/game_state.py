# server/logic/game_state.py
from collections import deque
import json
from server.config import GRID_WIDTH, GRID_HEIGHT

class Player:
    """Represents a player (a snake) in the Tron game."""
    def __init__(self, player_id, start_pos, start_dir):
        self.id = player_id
        self.body = deque([start_pos])
        self.direction = start_dir  # e.g., (0, 1) for DOWN
        self.is_alive = True
        self.length = 1
        self.move_decision = None # Stores the upcoming move

    @property
    def head(self):
        return self.body[0]

    def apply_move(self):
        """Applies the stored move decision to grow the snake."""
        new_head = (self.head[0] + self.direction[0], self.head[1] + self.direction[1])
        self.body.appendleft(new_head)
        self.length += 1

class GameState:
    """Manages the game board and collision detection."""
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def check_for_fatalities(self, p1, p2):
        """
        Checks for all possible collision types before players move.
        This is the primary collision logic for the simultaneous-move engine.
        """
        p1_next_head = (p1.head[0] + p1.direction[0], p1.head[1] + p1.direction[1])
        p2_next_head = (p2.head[0] + p2.direction[0], p2.head[1] + p2.direction[1])

        p1_is_fatal = False
        p2_is_fatal = False

        # 1. Wall collisions
        if not (0 <= p1_next_head[0] < self.width and 0 <= p1_next_head[1] < self.height):
            p1_is_fatal = True
        if not (0 <= p2_next_head[0] < self.width and 0 <= p2_next_head[1] < self.height):
            p2_is_fatal = True

        # 2. Body collisions (self and opponent)
        if not p1_is_fatal and (p1_next_head in p1.body or p1_next_head in p2.body):
            p1_is_fatal = True
        if not p2_is_fatal and (p2_next_head in p2.body or p2_next_head in p1.body):
            p2_is_fatal = True

        # 3. Head-on collision
        if p1_next_head == p2_next_head:
            p1_is_fatal = True
            p2_is_fatal = True

        if p1_is_fatal: p1.is_alive = False
        if p2_is_fatal: p2.is_alive = False


    def get_state_for_json(self, turn, p1, p2):
        """Creates a dictionary representing the current state for logging."""
        return {
            "turn": turn,
            "board": {"width": self.width, "height": self.height},
            "p0": {"id": "p0", "head": {"x": p1.head[0], "y": p1.head[1]}, "body": [{"x": pos[0], "y": pos[1]} for pos in p1.body], "alive": p1.is_alive},
            "p1": {"id": "p1", "head": {"x": p2.head[0], "y": p2.head[1]}, "body": [{"x": pos[0], "y": pos[1]} for pos in p2.body], "alive": p2.is_alive}
        }

    def get_json_for_bot(self, turn, you, opponent):
        """Creates the specific JSON string view for one bot."""
        grid = [[0 for _ in range(self.height)] for _ in range(self.width)]
        for part in you.body: grid[part[0]][part[1]] = 1
        for part in opponent.body: grid[part[0]][part[1]] = 2
        
        # Transpose the grid for the string representation if needed, or format as required.
        grid_str = ["".join(map(str, [grid[x][y] for x in range(self.width)])) for y in range(self.height)]

        bot_view = {
            "turn": turn,
            "board": {"width": self.width, "height": self.height, "grid": grid_str},
            "you": {"id": f"p{you.id}", "head": {"x": you.head[0], "y": you.head[1]}, "body": [{"x": pos[0], "y": pos[1]} for pos in you.body], "length": you.length},
            "opponent": {"id": f"p{opponent.id}", "head": {"x": opponent.head[0], "y": opponent.head[1]}, "body": [{"x": pos[0], "y": pos[1]} for pos in opponent.body], "length": opponent.length}
        }
        return json.dumps(bot_view) + "\n"