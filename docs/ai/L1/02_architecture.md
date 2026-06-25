# 02 · Architecture

> Two co-located processes. The browser talks only to Next.js `/api/*`, which rewrites to the FastAPI agent backend. The backend owns Agora tokens and the agent session, wiring a cascading STT→LLM→TTS pipeline with filler-words latency smoothing and graceful farewell exit.

## Topology

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js (web/)  ──rewrite──▶  Agent backend (server/, :8000)
                                 │  builds cascading pipeline:
                                 │    DeepgramSTT(nova-3) → OpenAI(gpt-4o-mini) → MiniMaxTTS
                                 │  filler_words: static phrase list during LLM latency
                                 │  farewell_config: graceful exit on stop
                                 ▼
                              Agora ConvoAI Cloud
                                 │  user speech → Deepgram STT (managed, nova-3)
                                 │  text → OpenAI assistant (Agora-managed, keyless)
                                 │    [filler phrase plays while LLM generates]
                                 │  response → MiniMax TTS (managed)
                                 ▼
                              User hears agent; RTM transcript + metrics → web UI
```

- **`web/`** — Next.js 16 / React 19 / TypeScript. Owns UI plus the RTC/RTM client lifecycle. Calls only `/api/*`.
- **`server/`** — Python FastAPI (:8000). Owns Agora token generation and agent session lifecycle. SDK: `agora-agents>=2.3.0` (`import agora_agent`).
- No `llm/` service, no mock vendor, no public tunnel — all three vendors are Agora-managed cloud services.

## Request lifecycle

1. Browser `GET /api/get_config` → Next rewrites to backend `/get_config`; backend mints a Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE` and returns channel + UIDs.
2. Browser joins the RTC channel, then `POST /api/startAgent`; backend builds the cascading vendor chain and starts an async agent session.
3. Agora runs Deepgram STT on user audio; the transcript goes to the managed OpenAI assistant; while the LLM is generating, Agora plays a randomly selected filler phrase.
4. The LLM response is synthesized via MiniMax TTS and played back into the channel.
5. RTM delivers transcript + metrics to the web UI.
6. `POST /api/stopAgent { agentId }` ends the session; `farewell_config` lets the agent speak a farewell before leaving the channel.

## Why no `llm/` service

This recipe uses only **Agora-managed vendors** (`DeepgramSTT`, `OpenAI`, `MiniMaxTTS` from `agora_agent.agentkit.vendors`). Agora holds the provider API keys on its cloud. The recipe is zero-key by default — only `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE` are required. An optional `OPENAI_API_KEY` lets you bring your own OpenAI account.

## Key abstractions

- **`Agent`** (`server/src/agent.py`) — async wrapper around `AgoraAgent`; owns the `AsyncAgora` client, env, and the in-memory `_sessions` map keyed by `agent_id`.
- **`build_filler_words()` / `build_farewell()`** (`server/src/filler_config.py`) — pure builder functions for the `filler_words` and `farewell_config` dicts passed to `AgoraAgent(...)`.
- **Rewrite proxy** (`web/next.config.ts`) — the only browser→backend boundary; no Next Route Handlers exist for agent/token logic.

## Tech decisions

- **Rewrites, not Route Handlers** — hides backend placement behind `/api/*` so the same client works locally and deployed (set `AGENT_BACKEND_URL`).
- **Filler words via static config** — `build_filler_words()` uses `mode: "static"` with a shuffled phrase list; the SDK (2.0.0) supports static mode only.
- **Farewell via `parameters`** — `farewell_config` is embedded in the `parameters` dict passed to `AgoraAgent(...)`; gives the agent a 5-second window to say goodbye.
- **Top-level VAD on `AgoraAgent`** — the cascading pipeline uses an explicit `turn_detection` config on `AgoraAgent(...)`, unlike the MLLM recipe where VAD is vendor-owned.

## Related Deep Dives

- [filler_words_config](L2/filler_words_config.md) — full filler/farewell builder details and customization.
- [session_lifecycle](L2/session_lifecycle.md) — browser orchestration of config + start/stop, RTC/RTM, transcript mapping.
