from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from server.games.base import GamePlugin, MatchConfig


BotStepFn = Callable[[int, str], str | None]


@dataclass
class RefereeResult:
    winner: str
    replay: str
    termination_reason: str


def run_referee_match(
    plugin: GamePlugin,
    config: MatchConfig,
    get_bot_action: BotStepFn,
) -> RefereeResult:
    """
    Generic referee loop. It knows nothing about game internals.
    `get_bot_action(player_index, bot_view_json)` should return normalized action strings.
    """
    state = plugin.create_initial_state(config)

    turn = 0
    frames = [plugin.to_replay_frame(state, turn)]

    while not plugin.is_terminal(state, turn, config):
        turn += 1

        p0_view = plugin.build_bot_view(state, turn, 0)
        p1_view = plugin.build_bot_view(state, turn, 1)

        p0_action = get_bot_action(0, p0_view)
        p1_action = get_bot_action(1, p1_view)

        plugin.validate_and_apply_actions(state, {0: p0_action, 1: p1_action})
        frames.append(plugin.to_replay_frame(state, turn))

    winner = plugin.winner_key(state)
    reason = plugin.termination_reason(state, turn, config)
    replay = json.dumps({"frames": frames, "result": {"winner": winner, "termination": reason}})

    return RefereeResult(winner=winner, replay=replay, termination_reason=reason)
