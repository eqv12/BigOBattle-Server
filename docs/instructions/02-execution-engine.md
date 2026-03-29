# The Execution Engine (The "Referee")

## Core Responsibility
The Execution Engine provides a secure environment for running adversarial user code (bots). It is the backbone of the platform's execution layer.

## Containerized Isolation & Security (Critical)
- **Zero Host Access:** All user-submitted code MUST execute within strictly isolated, ephemeral Docker containers. 
- **Resource Quotas:** Every bot execution is capped via Docker's memory flags (`--memory=256m`) and strict process-level timeouts (`FIRST_MOVE_TIMEOUT_S=3.0`, `MOVE_TIMEOUT_S=0.5`).
## Error Handling & Non-Blocking I/O
- **Error Envelopes:** Bots exceeding limits or encountering syntax errors are terminated. The engine captures `stderr` and specific Docker crash codes (e.g. 137 for OOM). It generates a structured JSON "Error Envelope" attached to the final `GameState.json` log, which the frontend uses to display precise UI error traces in the Monaco Editor.
- **Asynchronous Telemetry:** I/O streams (`stdout`/`stderr`) are read asynchronously to prevent engine deadlocks (for instance, when a bot outputs an unformatted string without a newline, or crashes violently without closing the stream).
- **Execution Logging:** The engine tracks precisely how long (in milliseconds) each move takes to compute, exposing this directly in the match replay for telemetry.

## Performance: The "Warm Pool" Strategy
- **Low Latency:** To drop match startup latency well under 500ms and eliminate heavy JVM/Compiler boot penalties during `FIRST_MOVE_TIMEOUT`, the architecture utilizes a "Warm Pool" strategy.
- **Dynamic Injection:** Instead of spawning ephemeral `docker run` containers for every match, the engine maintains pre-initialized, paused Docker containers ready to accept dynamic code injection.

## 100% Determinism (Reliability)
- **Reproducibility is Non-Negotiable:** The game engine processes inputs (bot commands) sequentially and deterministically.
- If a match is re-run with the same bot code and the exact same random seed, the outcome and `GameState.json` log MUST be bit-for-bit identical.

## Multi-Language Runtimes
- Platform natively supports Python, Java, C, C++, and JavaScript (Node.js).
- Achieved via a comprehensive execution image (`tron-local-env`) that packages requisite compilers and runtimes seamlessly into the warm pool.
