# The Execution Engine (The "Referee")

## Core Responsibility
The Execution Engine provides a secure, deterministic environment for running adversarial user code (bots). It is the backbone of the platform's fairness and technical merit.

## Containerized Isolation & Security (Critical)
- **Zero Host Access:** All user-submitted code MUST execute within strictly isolated, ephemeral Docker containers. The system must restrict access to the host file system and host network to prevent container escape attacks.
- **Resource Quotas:** Every bot execution must be aggressively capped:
  - Max RAM & Max CPU Time should be fixed but modular from an admin's account. 
- Bots exceeding limits must be forcefully terminated immediately and the other bot wins. Error events (e.g., syntax errors, OOM, timeouts) must return clean, parseable errors with precise line numbers and the raw error messages for easier debugging. (for Monaco Editor integration in the frontend).

## Performance: The "Warm Pool" Strategy
- Ensure match startup latency is under 500ms (aim for 2 seconds max startup time between request and first turn of simulation).
- The execution engine manages a pool of pre-initialized, paused Docker containers awaiting user code injection to eliminate cold-start delays.

## 100% Determinism (Reliability)
- **Reproducibility is Non-Negotiable.** The game engine must process inputs (bot commands) sequentially and deterministically.
- If a match is re-run with the same bot code and the exact same random seed, the outcome and `GameState.json` log MUST be bit-for-bit identical to the original match. Unless of course the bot itself is random in which case this it wont be identical. The system from our end must be deterministic.
