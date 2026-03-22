from server.games.registry import GameRegistry
from server.games.tron import TronPlugin


def build_default_registry() -> GameRegistry:
    registry = GameRegistry()
    registry.register(TronPlugin())
    return registry


__all__ = ["GameRegistry", "build_default_registry", "TronPlugin"]
