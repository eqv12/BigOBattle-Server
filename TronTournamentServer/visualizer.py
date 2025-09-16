import pygame
import json
import sys
import os
import argparse # REFACTORED: For better command-line arguments

# --- BOILERPLATE TO MAKE SCRIPT RUNNABLE ---
# This allows the script to find your server modules like `db_handler`
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
sys.path.insert(0, project_root)
# -------------------------------------------

from server.database import db_handler

# --- Constants ---
CELL_SIZE = 24
BACKGROUND_COLOR = (20, 20, 30)
GRID_LINE_COLOR = (40, 40, 50)
PLAYER_COLORS = {
    0: (66, 135, 245),  # Blue
    1: (245, 147, 66),  # Orange
}
PLAYBACK_SPEED_FPS = 12 # How many turns to show per second

def render_game(replay_data):
    """
    REFACTORED: This is the core rendering function.
    It takes a replay data dictionary and handles all the Pygame drawing.
    """
    # --- Initialization ---
    pygame.init()
    
    # REFACTORED: The new engine replay format has a different structure
    frames = replay_data.get('frames', [])
    if not frames:
        print("❌ Error: Replay data has no frames.")
        return

    first_frame = frames[0]
    grid_width = first_frame['board']['width']
    grid_height = first_frame['board']['height']

    screen_width = grid_width * CELL_SIZE
    screen_height = grid_height * CELL_SIZE
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption(f"Tron Replay Viewer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 30, bold=True)

    # --- Main Playback Loop ---
    frame_index = 0
    running = True
    paused = False
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_RIGHT:
                    frame_index = min(frame_index + 1, len(frames) - 1)
                if event.key == pygame.K_LEFT:
                    frame_index = max(frame_index - 1, 0)
                if event.key == pygame.K_ESCAPE:
                    running = False

        if paused:
            # Continue to draw the current frame when paused
            pass
        elif frame_index < len(frames) - 1:
            frame_index += 1

        # --- Drawing ---
        screen.fill(BACKGROUND_COLOR)
        
        current_frame = frames[frame_index]
        p0_data = current_frame.get('p0', {})
        p1_data = current_frame.get('p1', {})

        # Draw player 0's trail
        for part in p0_data.get('body', []):
            rect = pygame.Rect(part['x'] * CELL_SIZE, part['y'] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, PLAYER_COLORS[0], rect)
        
        # Draw player 1's trail
        for part in p1_data.get('body', []):
            rect = pygame.Rect(part['x'] * CELL_SIZE, part['y'] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, PLAYER_COLORS[1], rect)

        # Draw grid lines
        for x in range(0, screen_width, CELL_SIZE):
            pygame.draw.line(screen, GRID_LINE_COLOR, (x, 0), (x, screen_height))
        for y in range(0, screen_height, CELL_SIZE):
            pygame.draw.line(screen, GRID_LINE_COLOR, (0, y), (screen_width, y))
        
        # Display winner text if playback is finished
        if frame_index == len(frames) - 1:
            result = replay_data.get("result", {})
            winner_key = result.get("winner", "draw")
            
            if winner_key == 'p0':
                text = "Player 0 Wins!"
                color = PLAYER_COLORS[0]
            elif winner_key == 'p1':
                text = "Player 1 Wins!"
                color = PLAYER_COLORS[1]
            else:
                text = "DRAW"
                color = (200, 200, 200)

            text_surf = font.render(text, True, color)
            text_rect = text_surf.get_rect(center=(screen_width/2, screen_height/2))
            screen.blit(text_surf, text_rect)

        pygame.display.flip()
        clock.tick(PLAYBACK_SPEED_FPS)
        
    pygame.quit()

def visualize_from_file(filepath):
    """Loads a replay from a local JSON file."""
    print(f"📂 Loading replay from file: {filepath}")
    try:
        with open(filepath, 'r') as f:
            replay_data = json.load(f)
        render_game(replay_data)
    except FileNotFoundError:
        print(f"❌ Error: Replay file not found at '{filepath}'")
    except json.JSONDecodeError:
        print(f"❌ Error: Could not parse JSON from file '{filepath}'")

def visualize_from_db(match_id):
    """Loads a replay from the tournament database."""
    print(f"💾 Loading replay for Match ID {match_id} from database...")
    replay_json_string = db_handler.get_replay_data(match_id)
    
    if not replay_json_string:
        print(f"❌ Error: No replay found for Match ID {match_id} in the database.")
        return
    
    try:
        replay_data = json.loads(replay_json_string)
        render_game(replay_data)
    except json.JSONDecodeError:
        print(f"❌ Error: Could not parse JSON from database for Match ID {match_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tron Tournament Replay Visualizer")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=str, help="Path to a local replay JSON file.")
    group.add_argument("--db", type=int, help="The ID of the match to load from the database.")
    
    args = parser.parse_args()

    if args.file:
        visualize_from_file(args.file)
    elif args.db:
        visualize_from_db(args.db)