# 05 · Workflows

> Step-by-step guides for the common changes in this recipe. Each ends with the narrowest verify command to run.

## Add or change a browser-facing route

1. Add the FastAPI handler in `server/src/server.py` (return the `{ code, msg, data }` envelope).
2. Add the `/api/<name>` → `/<name>` mapping in `web/next.config.ts` `rewrites()`.
3. Add a client helper in `web/src/services/api.ts`.
4. Extend `web/scripts/verify-api-contracts.ts` with the new path + envelope assertions.
5. Verify: `bun run verify:web` (and `bun run verify:local:fastapi` if it should go through the real backend).

## Change filler phrases

1. Edit `FILLER_PHRASES` in `server/src/filler_config.py` — any non-empty list of strings.
2. Keep `mode: "static"` and `selection_rule: "shuffle"` unchanged — SDK 2.0.0 supports static mode only.
3. Verify: `cd server && pytest tests -v` (the phrase-count assertion in `test_filler_config.py` checks `>= 3`).

## Change farewell behavior

1. Edit `build_farewell()` in `server/src/filler_config.py`. Toggle `graceful_enabled` or adjust `graceful_timeout_seconds`.
2. Verify: `cd server && pytest tests -v`.

## Change the agent model, prompt, or greeting

1. Greeting: set `AGENT_GREETING` (env) or edit the default string in `server/src/agent.py`.
2. Model: set `OPENAI_MODEL` (default `gpt-4o-mini`).
3. System prompt: edit `AGENT_SYSTEM_PROMPT` in `server/src/agent.py`.
4. Verify: `bun run verify:backend` (compile) + `cd server && pytest tests -v`.

## Change the TTS voice

1. Set `TTS_VOICE` (default `English_captivating_female1`) to any valid MiniMax voice ID.
2. Or edit the default in `Agent.__init__` in `server/src/agent.py`.
3. Verify: `bun run verify:backend`.

## Adjust VAD / turn detection

1. Edit the `turn_detection` dict in `AgoraAgent(...)` inside `Agent.start()` in `server/src/agent.py`.
2. The dict is passed as a top-level argument (not inside a vendor); see [filler_words_config](L2/filler_words_config.md) for the full structure.
3. Verify: `bun run verify:local:fastapi`.

## Adjust session parameters (codec, scenario)

1. Edit the `parameters` dict in `Agent.start()` — `audio_scenario`, `data_channel`, `enable_metrics`, etc.
2. `output_audio_codec` is also accepted per-request via `parameters` on `POST /startAgent`.
3. Verify: `bun run verify:local:fastapi`.

## Run / debug locally

```bash
bun run dev              # both processes
bun run doctor:local     # check creds + .env.local before a live call
```

## Verify before finishing

| Change touches…              | Run                                                                 |
| ---------------------------- | ------------------------------------------------------------------- |
| Web only                     | `bun run verify:web`                                                 |
| Filler/farewell config       | `cd server && pytest tests -v`                                       |
| Backend logic / vendors      | `bun run verify:backend` + `cd server && pytest tests -v`            |
| Route/proxy boundary         | `bun run verify:web:proxy` and/or `bun run verify:local:fastapi`    |
| Anything end-to-end (local)  | `bun run verify:local`                                               |

## Deploy

1. Deploy `web/` as a Next.js app.
2. Deploy `server/` (or any reachable FastAPI host); the published backend-only image is `ghcr.io/AgoraIO-Conversational-AI/recipe-agent-filler-words` on `v*` tags.
3. Set `AGENT_BACKEND_URL` in the web deployment so rewrites reach the backend.

## Related Deep Dives

- [filler_words_config](L2/filler_words_config.md) — full filler/farewell and VAD config detail.
- [session_lifecycle](L2/session_lifecycle.md) — client-side join/renewal/teardown.
