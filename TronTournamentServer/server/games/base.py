from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class MatchConfig:
    """Game-agnostic match configuration passed to plugins."""

    seed: int
    max_turns: int


class GamePlugin(Protocol):
    """Contract for adding new games without changing orchestration."""

    game_key: str

    def create_initial_state(self, config: MatchConfig) -> Any:
        ...

    def build_bot_view(self, state: Any, turn: int, player_index: int) -> str:
        ...

    def validate_and_apply_actions(self, state: Any, actions: dict[int, Any]) -> None:
        ...

    def is_terminal(self, state: Any, turn: int, config: MatchConfig) -> bool:
        ...

    def winner_key(self, state: Any) -> str:
        """Return one of: 'p0', 'p1', 'draw'."""
        ...

    def termination_reason(self, state: Any, turn: int, config: MatchConfig) -> str:
        ...

    def to_replay_frame(self, state: Any, turn: int) -> dict[str, Any]:
        ...
