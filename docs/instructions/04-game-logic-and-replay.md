# Game Logic & Replay Visualization

## Modularity & Extensibility
- The platform evaluates the absolute skill of a developer by creating autonomous agents that adapt to changing environments. Let's make it easy to add new games over time.
- All core game logic (state representation, allowed moves, scoring) in `server/logic/` must be 100% decoupled from the Docker orchestration mechanism.
- Ensure that the execution orchestration simply runs `logic.step(bot_actions)` without knowing the specific contents of a given game. Swapping Game 1 for Game 2 should be trivial.

## The "Flight Recorder" (Replay System)
The Replay System is critical to the educational value of EMERGENT. The platform creates a new standard for debugging in competitive environments by generating exact **Turn-by-Turn Replay Logs**.
1.  **JSON Generation:** Upon match completion, the execution engine MUST generate a `GameState.json` file. This log contains the turn-by-turn history, board state, actions taken, and errors/penalties throughout the game.
2.  **Visualization Integration:** The web interface (Frontend React SPA) parses this JSON log to render a graphical, step-by-step playback of the match.
3.  **Use Case:** This allows students to pause, rewind, and perform "White Box" testing on their algorithms, explicitly visualizing why a strategy failed at any specific tick.

## Replay Envelope Requirements (Room + Multi-Game)
Every replay JSON should include enough metadata for future compatibility:
- `schema_version`
- `game_key`
- `room_code` (or room id)
- `frames` (turn-by-turn state)
- `result` (`winner`, `termination`)

For debugging and transparent judging, replay payload should also carry:
- per-turn bot output events (`turn_events`)
- raw bot outputs/errors (`bot_raw_outputs`), including stderr logs where available

This allows one visualizer pipeline to load replays from multiple games over time.

## Visualizer Decoupling Rule
- Visualizer logic must be game-specific and pluggable.
- Frontend replay rendering should dispatch by `game_key`/`visualizer_key` to the correct renderer.
- Adding a new game must add a new renderer module without changing existing game visualizers.
