# Architecture & Stack Overview

## Project Context
EMERGENT is a single-developer college project. It is a real-time, adversarial coding game platform where developers write autonomous agents (bots) to compete. 

## Deployment Strategy
- **Single-Server LAN Deployment:** This project prioritizes simplicity and avoids cloud-native or multi-server over-engineering. We use simple, robust patterns appropriate for a single-node deployment to keep development fast and maintainable.

## Core Stack
- **Backend Framework:** Python (FastAPI). Chosen for native ASGI (Asynchronous I/O) support to handle thousands of concurrent match requests and WebSockets without blocking threads.
- **Persistent Database:** PostgreSQL. Stores persistent data with relational integrity (User Profiles, Authentication Credentials, Match History).
- **In-Memory Cache & Queue:** Redis. Manages the high-speed Job Queue for the execution engine and caches the Real-Time Leaderboard for sub-millisecond read/write speeds.
- **Execution Infrastructure:** Docker. Provides sandboxed, ephemeral container environments for strictly isolated untrusted code execution.

## Modularity Goal
- The platform currently supports one game, but the architecture must allow for trivial addition of new games. Game logic must remain entirely decoupled from the execution orchestration.

## Other Directives
1. Preserve determinism and isolation. User code always runs in Docker with strict reproducibility.
2. Keep errors parseable. Runtime/sandbox failures should map cleanly to user-facing line-level feedback.

## Current Product Model (Room-First)
- **Competition scope is Room-based:** Rankings are tracked per room, not global.
- **Minimal auth by design:**
	- Admin creates room.
	- Server generates `room_code` and admin password.
	- Participants join via `room_code` and submit with a display name.
	- First submission for a display name sets a password; later submissions must use that same password.
- **Game selection is room-level:** Admin picks the room's game at creation time.

## Structure Direction (Multi-Game)
- Keep orchestration generic and game-agnostic.
- Introduce a game plugin boundary (`games/base`, `games/registry`, `games/<game>/plugin`).
- CPU benchmark bots must be organized per game (not in one shared flat bucket).
