# Standardized Skill Assessment & Leaderboard

## Glicko-2 & Rating System
Instead of binary "Solved / Not Solved" tests, EMERGENT evaluates a user's absolute engineering mastery through a Continuous Elo/Glicko-2 Rating System.
- Submissions face other human-submitted bots (and/or benchmark bots).
- After every match, a Glicko-2 system calculates ratings asynchronously, updating a global leaderboard in real-time (cached in Redis).
- This produces a quantifiable metric for "engineering resilience."

## The Benchmark Bot Suite
We measure developer proficiency against fixed benchmarks to generate initial Elo ratings. The system ships with a Standardized Benchmark Bot Suite containing three distinct AI strategies.
1.  **Tier 1:** Serves as the fixed, basic "Ruler." Tests if a bot executes without crashing.
2.  **Tier 2:** Prioritizes the immediate optimal action without long-term foresight. Tests a student's basic heuristics and optimization logic.

3.  **Tier 3:** The toughest AI benchmark simulating full adversarial foresight. Tests a developer's grasp of distributed systems complexity and advanced game theory.

These CPU bots act as the baseline opponents for "Test" runs.

## Current Scope Decision: Room-Only Ratings
- Ratings are maintained per room leaderboard only.
- No global cross-room rating aggregation in current MVP.
- A participant can have independent ratings in different rooms.

## Practical Implementation Notes
- Persist Glicko-2 values per room-participant tuple.
- Match updates should only touch ratings inside the match's room.
