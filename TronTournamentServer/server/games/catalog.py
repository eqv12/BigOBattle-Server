from __future__ import annotations

from typing import Any


GAMES: dict[str, dict[str, Any]] = {
    "tron": {
        "key": "tron",
        "title": "Tron",
        "thumbnail": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&w=1200&q=60",
        "summary": "Grid survival duel with simultaneous turns.",
        "rules": [
            "Each bot receives JSON turn state on stdin and outputs JSON move.",
            "Allowed moves are UP, DOWN, LEFT, RIGHT.",
            "Collision with wall or any trail is fatal.",
            "If both collide simultaneously the result is draw.",
            "Timeouts and malformed output are treated as failures.",
        ],
        "bot_io": {
            "input": "JSON turn state via stdin",
            "output": "JSON object with `move` key",
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
