from __future__ import annotations

from typing import Dict

from server.games.base import GamePlugin


class GameRegistry:
    """Simple in-memory registry for game plugins."""

    def __init__(self) -> None:
        self._plugins: Dict[str, GamePlugin] = {}

    def register(self, plugin: GamePlugin) -> None:
        key = plugin.game_key.strip().lower()
        if not key:
            raise ValueError("game_key must be non-empty")
        self._plugins[key] = plugin

    def get(self, game_key: str) -> GamePlugin:
        key = game_key.strip().lower()
        if key not in self._plugins:
            raise KeyError(f"Unknown game_key: {game_key}")
        return self._plugins[key]

    def keys(self) -> list[str]:
        return sorted(self._plugins.keys())
