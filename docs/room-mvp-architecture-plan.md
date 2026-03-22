# Room-Only Multi-Game MVP Plan

Date: 2026-03-21
Decision: room-only ratings, minimal auth, higher stabilization priority, keep Flask in this refactor phase.

## 1) Product model (agreed)
- Admin creates a room.
- System returns room code + admin password.
- Admin picks the game for that room.
- Users join room via room code and submit bots under a display name.
- First submission sets password for that display name within that room.
- Later submissions require that same password.
- Leaderboard is room-scoped only.

## 2) Why keep Flask for now
- Current codebase is Flask-first; refactoring game boundaries + data model is already large.
- Migrating framework now adds risk and slows stabilization.
- We can keep API design framework-agnostic and migrate to FastAPI after core modularization.

## 3) Target structure
- TronTournamentServer/server/app.py (new API entrypoint)
- TronTournamentServer/server/api/
  - rooms.py
  - submissions.py
  - leaderboard.py
  - matches.py
- TronTournamentServer/server/services/
  - room_service.py
  - submission_service.py
  - matchmaking_service.py
  - rating_service.py
- TronTournamentServer/server/engine/
  - referee.py
  - sandbox.py
  - worker.py
- TronTournamentServer/server/games/
  - base.py
  - registry.py
  - tron/plugin.py
  - game2/plugin.py (future)
- TronTournamentServer/server/database/
  - schema.sql
  - migrations/
  - db_handler.py

## 4) Data model migration (room-first)
Add tables:
- rooms(id, room_code UNIQUE, admin_password_hash, game_key, created_at, status)
- participants(id, room_id, display_name, password_hash, active_bot_path, created_at, last_submission_at)
- room_ratings(id, room_id, participant_id, rating, rd, vol, matches_played, last_played_at)
- room_matches(id, room_id, game_key, participant_a_id, participant_b_id, winner_participant_id NULL, replay_data, termination_reason, played_at)

Notes:
- Keep existing tables during migration.
- Add compatibility read paths while switching endpoints.

## 5) API contract (minimal)
- POST /api/rooms
  - body: { game_key }
  - returns: { room_code, admin_password }
- POST /api/rooms/{room_code}/join
  - body: { display_name }
  - returns: { participant_id }
- POST /api/rooms/{room_code}/submit
  - multipart: bot_zip_file + display_name + password
  - first submit: creates participant password
  - later submits: verifies password
- GET /api/rooms/{room_code}/leaderboard
- GET /api/rooms/{room_code}/matches/recent
- POST /api/rooms/{room_code}/queue-match
- POST /api/rooms/{room_code}/test
  - quick unranked test vs benchmark/self (optional)

Legacy note:
- Old endpoints `/submit`, `/leaderboard`, `/test` are deprecated/removed.

## 6) Execution & matchmaking behavior
- Keep simple queue workers.
- Matchmaking remains room-scoped and pragmatic:
  - avoid immediate rematch loops
  - one active job per participant
  - simple candidate ordering by RD + recency
- No strict production-grade anti-abuse at this stage.

## 7) Stabilization-first phases
Phase 0: boundaries + adapters
- Introduce game plugin contract and registry.
- Wrap current Tron logic behind plugin.
- Add generic referee loop.

Phase 1: DB migration
- Add room tables and migration utility.
- Add room/participant CRUD in db_handler.

Phase 2: API routes
- Implement room create/join/submit/leaderboard routes.
- Keep existing routes temporarily for compatibility.

Phase 3: worker wiring
- Use room_matches queue payloads.
- Update ratings using existing Glicko2 core, now room-scoped.

Phase 4: UI overhaul
- Replace current placeholder UI with room-centric flow.
- Pages: Create Room, Join Room, Submit Bot, Leaderboard + recent matches.

Phase 5: hardening
- Determinism checks.
- Replay schema versioning.
- Better parseable error payloads for syntax/runtime/timeout.

## 8) First implementation milestone
Milestone A (start here):
- Working end-to-end for one room and one game (Tron plugin):
  create room -> join -> submit -> queue match -> replay + room leaderboard update.

Acceptance:
- Two users in same room can submit and get ranked.
- Wrong password on resubmit is rejected.
- Replay JSON persists and can be fetched.
