# Match Workflow & Queuing System

## High-Level Workflow Overview
1.  **User Action:** A user writes code in the browser IDE (React, not in this repo) and clicks either **"Test"** or **"Submit"**.
2.  **Dispatching:** The backend OpenAPI receives the command and routes the request into a Redis queue.
3.  **Referee Orchestration:** The engine grabs the queued code, spins up a Docker container, executes the simulation, logs the output JSON, and updates the leaderboard.

## The Priority Queue (Redis)
The core of this system is the Redis Asynchronous Match Queue. We must handle sudden spikes in requests gracefully by queueing jobs without blocking main server threads or crashing the backend.

### Async Priority:
- **Test Actions:** Users testing their code face predefined, tiered CPU Benchmark Bots. These matches are **high-priority** and **low-latency**. Fast execution allows users to get immediate debugging feedback and see how the bot performs via the visualizer.
- **Submit Actions:** Users submitting code face other human-submitted bots for official ranking. These matches are standard-priority and run asynchronously to update the global leaderboard.

## Scalability Constraint
The backend architecture (single-server LAN deployment) as much concurrent matches as possible. We need to keep the system lean and efficient and fast.

## Room Workflow (Current)
1. **Admin Creates Room:** backend generates room code and admin password, and stores selected game key.
2. **Participant Joins Room:** participant provides display name and room code.
3. **Participant Submits Bot:**
	 - First submit for `(room_code, display_name)` sets password.
	 - Next submits require password verification.
4. **Dispatching:** submit jobs enqueue room-scoped match requests.
5. **Referee Execution:** workers run matches only within the room and selected game.
6. **Room Leaderboard Update:** rating updates are written only to that room context.

## Matchmaking Policy (Pragmatic for MVP)
- Keep matchmaking simple and stable, not production-grade strict.
- Constraints:
	- no self-play
	- avoid immediate repeat pairings when practical
	- one active match job per participant at a time
	- prioritize participants with high RD / low recent activity
