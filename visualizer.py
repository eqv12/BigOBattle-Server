import pygame
import json
import sys
import time

# --- Constants ---
CELL_SIZE = 24
BACKGROUND_COLOR = (20, 20, 30)
GRID_LINE_COLOR = (40, 40, 50)
PLAYER_COLORS = {
    0: (66, 135, 245),  # Blue
    1: (245, 147, 66),  # Orange
}
PLAYBACK_SPEED_FPS = 12 # How many turns to show per second

def run_visualizer(log_filepath):
    """Loads a game replay file and plays back the Tron match."""
    try:
        with open(log_filepath, 'r') as f:
            log = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Replay file not found at '{log_filepath}'")
        return

    # --- Initialization ---
    pygame.init()
    grid_width, grid_height = log['grid_size']
    screen_width = grid_width * CELL_SIZE
    screen_height = grid_height * CELL_SIZE
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption(f"Tron Replay: Match {log.get('winner_id', -1)}")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 30, bold=True)

    # --- Prepare path data ---
    player_paths = {p['id']: p['path'] for p in log['players']}
    total_frames = max(len(p) for p in player_paths.values()) if player_paths else 0

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
                if event.key == pygame.K_ESCAPE:
                    running = False

        if paused:
            clock.tick(30) # Keep responding to events even when paused
            continue

        # --- Drawing ---
        screen.fill(BACKGROUND_COLOR)
        
        # Draw the trails up to the current frame
        for player_id, path in player_paths.items():
            color = PLAYER_COLORS.get(player_id, (255, 255, 255))
            # Draw only the portion of the path that has occurred
            for i in range(min(frame_index, len(path))):
                x, y = path[i]
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, color, rect)

        # Draw grid lines
        for x in range(0, screen_width, CELL_SIZE):
            pygame.draw.line(screen, GRID_LINE_COLOR, (x, 0), (x, screen_height))
        for y in range(0, screen_height, CELL_SIZE):
            pygame.draw.line(screen, GRID_LINE_COLOR, (0, y), (screen_width, y))

        # Check if playback is finished
        if frame_index >= total_frames:
            winner_id = log.get("winner_id", -1)
            text = f"Player {winner_id} Wins!" if winner_id != -1 else "DRAW"
            text_surf = font.render(text, True, PLAYER_COLORS.get(winner_id, (255, 255, 255)))
            text_rect = text_surf.get_rect(center=(screen_width/2, screen_height/2))
            screen.blit(text_surf, text_rect)
        else:
            frame_index += 1

        pygame.display.flip()
        clock.tick(PLAYBACK_SPEED_FPS)
        
    pygame.quit()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python visualizer.py <path_to_replay_file.json>")
    else:
        run_visualizer(sys.argv[1])

### **How to Run Your Test**

# 1.  **Save the Files:** Make sure `run_test_match.sh` and `visualizer.py` are saved in the root of your `TronTournamentServer` folder.
# 2.  **Make Executable:** Open Git Bash in your project folder and run `chmod +x run_test_match.sh`.
# 3.  **Launch the Test:** From the same Git Bash terminal, run the single master command:
#     ```bash
#     ./run_test_match.sh