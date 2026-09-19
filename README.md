# Agora Conversational AI — Filler Words Recipe (Python)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Bun](https://img.shields.io/badge/bun-latest-black)](https://bun.sh/)

The **filler words** recipe in the Agora Conversational AI recipes family.
A friendly voice agent that plays natural filler phrases during LLM latency
gaps and says a graceful goodbye when the conversation ends. Static filler mode
is **zero-key** by default because the main OpenAI vendor is Agora-managed.
Engine 2.12 generated fillers are available as an opt-in mode and use the
SDK's default Engine-managed generator. No filler LLM URL, API key, or model
needs to be configured.

**Pipeline:** `DeepgramSTT(nova-3)` → `OpenAI` (friendly assistant) → `MiniMaxTTS`

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Bun](https://bun.sh/)
- [Agora CLI](https://github.com/AgoraIO/cli) — makes generating an App ID + App Certificate easy

The same commands work on macOS, Linux, and Windows. On macOS/Linux, setup uses
`python3`; on Windows, it uses the Python launcher (`py`) or `python`. WSL and
virtualenv activation are not required.

## Run It

```bash
# 1. Install web deps + create the Python venv
bun run setup

# 2. Add Agora credentials (CLI), or edit server/.env.local by hand
agora login
agora project use <your-project>          # select which project to use
agora project env write server/.env.local # writes App ID + Certificate

# 3. Run backend + web
bun run dev
```

Open [http://localhost:3000](http://localhost:3000), choose **Static** or
**Generated** under **Filler mode**, then click **Start Conversation**. Ask
anything and listen for filler phrases between your question and the agent's
answer. The initial selection follows `FILLER_WORDS_MODE` in `server/.env.local`
(`static` when unset); you can switch modes before each conversation. Restart
the backend and refresh the page after changing the environment default.

### Working from a clone

If you cloned this repo (rather than scaffolding via the Agora CLI), the steps
above are complete as written: `bun run setup` creates the Python venv and
installs web dependencies, then `bun run dev` brings up both services. You
still need Agora credentials in `server/.env.local` before a conversation can
connect.

Services:

- Frontend — http://localhost:3000
- Backend — http://localhost:8000
- Mock LLM — N/A for the default Engine-managed path
- API docs — http://localhost:8000/docs

## Deploy

Deploy `web` (Next.js) and `server` (a reachable FastAPI backend). Set
`AGENT_BACKEND_URL` in the web deployment so the Next rewrites reach the backend.

A backend-only Docker image is published to
`ghcr.io/AgoraIO-Conversational-AI/recipe-agent-filler-words` on `v*` tags.
It exposes **BACKEND-ONLY** (:8000). No separate LLM container is needed for
static mode or the default Engine-managed generated mode.

## Environment variables

Backend env file: [`server/.env.example`](server/.env.example).

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | yes | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | yes | — | Agora Console → Project → App Certificate |
| `OPENAI_MODEL` | | `gpt-4o-mini` | OpenAI model for the assistant |
| `OPENAI_API_KEY` | | — | Optional — Agora manages the OpenAI key by default (keyless). Set only if your account requires it. |
| `FILLER_WORDS_MODE` | | `static` | Initial web selection and default for API requests that omit `fillerWordsMode`; accepts `static` or `generated`. A manual selection takes precedence for that conversation. |
| `TTS_VOICE` | | `English_captivating_female1` | MiniMax TTS voice |
| `AGENT_GREETING` | | built-in | Optional opening line override |

Generated mode has a built-in short-filler prompt and uses the SDK's default
Engine-managed generator. `FILLER_LLM_*` variables are no longer used; existing
values can be removed. Both modes use a 1500 ms response-wait trigger, matching
the Engine default. If the primary LLM produces content before that deadline,
no filler plays. In Generated mode, filler generation runs in parallel with the
primary LLM and uses up to four recent messages, capped at 1000 characters. At
the deadline, Engine plays a ready generated phrase or a built-in static fallback
if generation is not ready, fails, or returns empty text.

## Commands

```bash
bun run setup            # install web deps + create server/ venv
bun run dev              # run backend (:8000) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials checks

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:backend:pytest # standalone backend tests, no Agora cloud calls
bun run verify:local     # full local gate: backend compile + smoke tests + web build
bun run clean            # remove venvs and build artifacts
```

Tests run standalone (no Agora cloud needed): `pytest` in `server/`, plus
`bun run verify` in `web/`. CI runs them on Linux/macOS/Windows × Python 3.10 & 3.13.

To verify generated filler configuration locally without cloud credentials:

```bash
bun run verify:backend:pytest
```

For an end-to-end check with an App ID that has an Engine generator provisioned,
select **Generated** in the web UI and start a conversation. API callers can send
`"fillerWordsMode": "generated"` to `/startAgent`, or omit it and set the backend
default:

```env
FILLER_WORDS_MODE=generated
```

No custom filler endpoint or public tunnel is required.

## Architecture

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session (managed OpenAI vendor)
                          │  filler_words: static or generated phrases during LLM latency
                          │  farewell_config: graceful exit on stop
                          ▼
                       Agora ConvoAI Cloud
                          │  Deepgram STT (managed, nova-3)
                          │  OpenAI assistant (Agora-managed, keyless)
                          │  MiniMax TTS (managed)
                          ▼
                       User hears the agent (with filler phrases during latency)
```

No separate `llm/` service — OpenAI is Agora-managed and requires no API key.
See [ARCHITECTURE.md](./ARCHITECTURE.md).

## What You Get

- A **Next.js** web client (:3000) that drives the RTC/RTM lifecycle and only ever calls `/api/*`.
- A **FastAPI** agent backend (:8000) that owns Agora token generation and the agent session lifecycle.
- The `/api/filler_config` · `/api/get_config` · `/api/startAgent` · `/api/stopAgent` contract between the web client and the backend (Next rewrites, no Route Handlers).
- **Managed keyless OpenAI** powering the assistant — Agora-managed, no `OPENAI_API_KEY` required.
- **filler_words** selectable Static or Generated mode before each conversation, with a static fallback for generated phrases.
- **farewell_config** graceful exit: the agent speaks a farewell before leaving the channel.
- **Zero-key** setup — the full pipeline runs with no LLM API key by default.

## How It Works

1. The browser reads `/api/filler_config` to initialize the mode selector from
   `FILLER_WORDS_MODE`. When the user starts a conversation, it calls
   `/api/get_config`; the backend mints an Agora token from `AGORA_APP_ID` +
   `AGORA_APP_CERTIFICATE`.
2. The browser calls `/api/startAgent` with the selected `fillerWordsMode` and
   connects to RTC/RTM; the backend starts an agent session using the managed
   OpenAI vendor with `filler_words` and `farewell_config` configured.
3. The user speaks. Agora runs STT (Deepgram, nova-3) and produces a transcript.
4. While the LLM is generating a response, Agora either plays a randomly
   selected static phrase or asks the SDK's default Engine-managed generator
   for a short phrase. Generated mode falls back to the
   static list when generation is not ready, fails, or returns empty text.
5. The LLM response arrives and is spoken via MiniMax TTS.
6. `/api/stopAgent` ends the session. The agent speaks a farewell
   (`farewell_config`) before leaving the channel.

## Repo Map

- `web/` — Next.js frontend (:3000); RTC/RTM lifecycle and UI.
- `server/` — FastAPI agent backend (:8000); Agora tokens + agent lifecycle, managed OpenAI assistant.
- `ARCHITECTURE.md` — system shape and component boundaries.
- `AGENTS.md` — guide for coding agents working in this repo.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Initial mode does not match `.env.local` | Set `FILLER_WORDS_MODE` in `server/.env.local`, restart the backend, and refresh the page. If `server/.env` also exists, its values override `.env.local`. |
| No filler phrases heard | Fillers play only if the primary LLM is still pending at the deadline, not before every answer or greeting. Both modes use `FILLER_RESPONSE_WAIT_MS = 1500` in `server/src/filler_config.py`; restart the backend and start a new conversation after changing it. Startup logs show `filler_mode` and `response_wait_ms`. |
| Generated mode plays a built-in phrase | This is the static fallback: generation was not ready, failed, or returned empty text at the deadline. A shorter wait makes this fallback more likely. |
| Generated mode does not start | Check that the App ID has the Engine generator enabled. No `FILLER_LLM_BASE_URL` is needed. |
| No farewell on hang-up | Verify `farewell_config.graceful_enabled` is `true`; the agent needs a moment (`graceful_timeout_seconds`) to speak before it exits. |
| Local calls fail under a global proxy (Clash, etc.) | Configure your proxy to send `127.0.0.1`, `localhost`, and RFC-1918 ranges DIRECT. |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
