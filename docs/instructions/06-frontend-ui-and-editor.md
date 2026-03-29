# Frontend UI, Navigation, and Editor Experience

## Product Direction
Frontend should be built as a React single-page app (SPA), not plain server-rendered templates.

Reasoning:
- We need a multi-screen UX with stateful flows (landing, game catalog, room join/create, editor workspace).
- Monaco integration is significantly cleaner in React.
- Replay/log/editor tabs and room state updates are easier to maintain in a component model.

## Core UX Flow (Room-First)
1. Landing page ("The Ad"):
   - Should be an attractive, scrollable page built to sell the platform.
   - Includes a Hero section ("Code. Compete. Conquer."), Feature highlights, and clear CTAs.
   - Primary CTAs: Create Room, Join Room, Browse Games.
   - Top navigation: Games, Join Room, Create Room, About.
2. Games page:
   - Beautiful Card-based game gallery with thumbnail/cover, short description, and tags (e.g. 1v1, Grid-based).
   - Card styling will include hover effects (via Framer Motion/Tailwind).
   - Clicking a card opens Game Details page. (No dropdown selection flow).
3. Game details page:
   - Rules, format, turn model, bot I/O contract.
   - "Create Room" CTA must be sticky and visible regardless of scroll depth.
4. Create Room page:
   - Directs users to the Browse Games page if no game is selected.
   - Once a game is selected, instantly generates room code and admin PIN.
5. Join Room flow (2-Step):
   - Step 1: Clean, centered form to enter room code and display name (no avatars yet, just initials).
   - Step 2: "Ready Room" lobby screen displaying the game rules context natively before entering the workspace.
   - Final CTA: "Enter Workspace / Start".
6. Workspace page:
   - Monaco editor integrated.
   - Primary actions: Test, Submit.
   - Test has tier selector (Tier 1/2/3 benchmark selection).
   - Output area with tabs: Replay, Logs, Raw Output.

## UI/UX Technology Guidelines
- **Framework & Styling**: React SPA (Vite) styled with **Tailwind CSS**.
- **Icons**: Use **Lucide-React** for clean, consistent, and modern iconography.
- **Animations**: Use **Framer Motion** for subtle page transitions and hover states.
- **Visual Aesthetic**: Opt for a "Hacker / Developer" dark-mode theme, using deep backgrounds with neon electric blue/green accents, ensuring the code editor feels highly integrated into the site.

## UI Requirements
- Desktop and mobile responsive.
- Intentional visual design (not generic/default template look).
- Navigation state and selected room/game should persist in local state and localStorage where useful.
- API errors must display cleanly in-page (never only console logs).

## API/Contract Implications
- Existing backend room APIs remain canonical:
  - POST /api/rooms
  - POST /api/rooms/{room_code}/join
  - POST /api/rooms/{room_code}/submit
  - GET /api/rooms/{room_code}/leaderboard
  - GET /api/rooms/{room_code}/matches/recent
  - POST /api/rooms/{room_code}/queue-match
- Additional APIs required for full editor workflow:
  - GET /api/games
  - GET /api/games/{game_key}
  - POST /api/rooms/{room_code}/test (tier-aware)
  - GET /api/rooms/{room_code}/replays/{match_id} (or include replay payload in recent matches)
  - GET /api/rooms/{room_code}/logs/{job_or_match_id} for raw logs

## Monaco and Workspace Notes
- Preferred package: @monaco-editor/react.
- Workspace must be language-agnostic for at least: Python, Java, C.
- Editor language selector must switch templates and submission packaging rules by language.
- Submission ZIP should include language-appropriate starter files and `run.sh`.
- Keep editor content per room/game in localStorage for draft recovery.
- Submission package generation can start with ZIP upload path, then optionally add in-browser packaging later.

## Language UX Rules
- Supported languages: `python`, `java`, `c`.
- Workspace should expose a language selector and persist per-room language choice.
- Starter templates should be explicit:
   - Python: `bot.py` + `run.sh` (`python3 bot.py`)
   - Java: `Main.java` + `run.sh` (`javac Main.java && java Main`)
   - C: `bot.c` + `run.sh` (`gcc bot.c -O2 -o bot && ./bot`)

## Scope and Sequencing
- React migration is approved and preferred.
- Existing Flask template/static UI is transitional and can be replaced.
- Prioritize a clean frontend architecture over short-term patching.

## Out of Scope (for now)
- Full production authentication and security hardening.
- Multi-room concurrent collaboration features.
- WebSocket-only realtime updates (polling acceptable initially).
