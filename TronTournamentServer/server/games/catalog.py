from __future__ import annotations

from typing import Any


GAMES: dict[str, dict[str, Any]] = {
    "tron": {
        "key": "tron",
        "title": "Tron",
        "thumbnail": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1200&q=80",
        "summary": "Grid survival duel with simultaneous turns.",
        "description": "Welcome to the neon grid! Two autonomous light cycles are dropped into an enclosed arena, moving simultaneously at breakneck speeds and leaving deadly solid trails of light behind them. Your objective is simple: outlast your opponent. To win, you must write an intelligent algorithm that outmaneuvers your adversary, boxes them in, and forces them to crash into a wall or a trail. Spatial awareness, predicting enemy movements, and controlling the board are key to your survival.",
        "rules": [
            "Each bot receives a JSON turn state via stdin and must output a JSON move.",
            "Allowed moves are UP, DOWN, LEFT, RIGHT.",
            "Collision with wall or any trail is fatal.",
            "If both collide simultaneously the result is draw.",
            "Timeouts and malformed output are treated as failures.",
        ],
        "bot_io": {
            "input": """{
  "turn": 1,
  "board": {
    "width": 15,
    "height": 15,
    "grid": [
      "000000000000000",
      "001111111111000",
      ...
    ]
  },
  "you": {
    "id": "p0",
    "head": {"x": 5, "y": 5},
    "body": [{"x": 5, "y": 5}, ...],
    "length": 1
  },
  "opponent": {
    "id": "p1",
    "head": {"x": 10, "y": 10},
    "body": [{"x": 10, "y": 10}, ...],
    "length": 1
  }
}""",
            "output": """{
  "move": "UP" // Allowed: "UP", "DOWN", "LEFT", "RIGHT"
}""",
        },
        "visualizer_key": "tron",
        "supported_languages": ["python", "java", "c"],
    }
}


def list_games() -> list[dict[str, Any]]:
    return [
        {
            "key": game["key"],
            "title": game["title"],
            "thumbnail": game["thumbnail"],
            "summary": game["summary"],
            "visualizer_key": game["visualizer_key"],
            "supported_languages": game["supported_languages"],
        }
        for game in GAMES.values()
    ]


def get_game(game_key: str) -> dict[str, Any] | None:
    return GAMES.get(game_key.strip().lower())
