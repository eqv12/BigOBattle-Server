from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Any

from server.config import GRID_HEIGHT, GRID_WIDTH
from server.games.base import GamePlugin, MatchConfig
from server.logic.game_state import GameState, Player


MOVE_MAP: dict[str, tuple[int, int]] = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0),
}


@dataclass
class TronState:
    game_state: GameState
    players: list[Player]
    winner: str = "draw"
    reason: str = "Max turns reached"


class TronPlugin(GamePlugin):
    game_key = "tron"

    def create_initial_state(self, config: MatchConfig) -> TronState:
        rng = random.Random(config.seed)
        p0_start, p1_start = self._get_symmetric_start_positions(
            width=GRID_WIDTH,
            height=GRID_HEIGHT,
            padding=5,
            rng=rng,
        )
        players = [
            Player(0, p0_start, (1, 0)),
            Player(1, p1_start, (-1, 0)),
        ]
        return TronState(game_state=GameState(GRID_WIDTH, GRID_HEIGHT), players=players)

    def build_bot_view(self, state: TronState, turn: int, player_index: int) -> str:
        you = state.players[player_index]
        opp = state.players[1 - player_index]
        return state.game_state.get_json_for_bot(turn, you, opp)

    def validate_and_apply_actions(self, state: TronState, actions: dict[int, Any]) -> None:
        # Disqualify invalid move payloads.
        for idx, action in actions.items():
            move = action if isinstance(action, str) else None
            if move not in MOVE_MAP:
                state.players[idx].is_alive = False
                state.reason = f"p{idx} invalid move"

        if not all(p.is_alive for p in state.players):
            state.winner = self._winner_from_alive(state)
            return

        state.players[0].direction = MOVE_MAP[str(actions[0])]
        state.players[1].direction = MOVE_MAP[str(actions[1])]

        state.game_state.check_for_fatalities(state.players[0], state.players[1])

        if state.players[0].is_alive:
            state.players[0].apply_move()
        if state.players[1].is_alive:
            state.players[1].apply_move()

        if not all(p.is_alive for p in state.players):
            state.winner = self._winner_from_alive(state)
            if state.winner == "draw":
                state.reason = "Head-on collision or mutual elimination"
            elif state.winner == "p0":
                state.reason = "p1 collision"
            else:
                state.reason = "p0 collision"

    def is_terminal(self, state: TronState, turn: int, config: MatchConfig) -> bool:
        return (not all(p.is_alive for p in state.players)) or (turn >= config.max_turns)

    def winner_key(self, state: TronState) -> str:
        return state.winner if state.winner in {"p0", "p1", "draw"} else "draw"

    def termination_reason(self, state: TronState, turn: int, config: MatchConfig) -> str:
        if turn >= config.max_turns and all(p.is_alive for p in state.players):
            return "Max turns reached"
        return state.reason

    def to_replay_frame(self, state: TronState, turn: int) -> dict[str, Any]:
        return state.game_state.get_state_for_json(turn, state.players[0], state.players[1])

    @staticmethod
    def _winner_from_alive(state: TronState) -> str:
        p0_alive = state.players[0].is_alive
        p1_alive = state.players[1].is_alive
        if p0_alive and not p1_alive:
            return "p0"
        if p1_alive and not p0_alive:
            return "p1"
        return "draw"

    @staticmethod
    def _get_symmetric_start_positions(width: int, height: int, padding: int, rng: random.Random) -> tuple[tuple[int, int], tuple[int, int]]:
        p0_x = rng.randint(padding, (width // 2) - padding)
        p0_y = rng.randint(padding, height - 1 - padding)

        p1_x = width - 1 - p0_x
        p1_y = p0_y

        return (p0_x, p0_y), (p1_x, p1_y)


def build_tron_replay_json(frames: list[dict[str, Any]], winner: str, reason: str) -> str:
    return json.dumps({"frames": frames, "result": {"winner": winner, "termination": reason}})
