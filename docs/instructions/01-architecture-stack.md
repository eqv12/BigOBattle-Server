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
