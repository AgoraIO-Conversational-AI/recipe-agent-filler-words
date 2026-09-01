# Agora Conversational AI — Filler Words Recipe (Python)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Bun](https://img.shields.io/badge/bun-latest-black)](https://bun.sh/)

The **filler words** recipe in the Agora Conversational AI recipes family.
A friendly voice agent that plays natural filler phrases during LLM latency
gaps and says a graceful goodbye when the conversation ends. Static filler mode
is **zero-key** by default because the main OpenAI vendor is Agora-managed.
Engine 2.12 generated fillers are available as an opt-in mode and use the
generator provisioned for the App ID by default. Developers can optionally
override it with an OpenAI-compatible provider.

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

Open [http://localhost:3000](http://localhost:3000) → **Start Conversation** →
ask anything and listen for filler phrases between your question and the agent's
answer.

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
| `FILLER_WORDS_MODE` | | `static` | `static` uses the built-in phrases; `generated` enables Engine 2.12 generated fillers. |
| `FILLER_LLM_BASE_URL` | | — | Optional BYO provider URL; set all three `FILLER_LLM_*` fields together. |
| `FILLER_LLM_API_KEY` | | — | Optional BYO provider key; never commit it. |
| `FILLER_LLM_MODEL` | | — | Optional BYO provider model. |
| `TTS_VOICE` | | `English_captivating_female1` | MiniMax TTS voice |
| `AGENT_GREETING` | | built-in | Optional opening line override |

Generated mode has a built-in short-filler prompt. With no `FILLER_LLM_*`
fields, Engine uses the generator provisioned for the App ID. Set all three
fields to use a third-party public OpenAI-compatible provider instead. Generated
fillers use a fixed 1500 ms response-wait trigger.

## Commands

```bash
bun run setup            # install web deps + create server/ venv
bun run dev              # run backend (:8000) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials checks

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:local     # full local gate: backend compile + smoke tests + web build
bun run clean            # remove venvs and build artifacts
```

Tests run standalone (no Agora cloud needed): `pytest` in `server/`, plus
`bun run verify` in `web/`. CI runs them on Linux/macOS/Windows × Python 3.10 & 3.13.

To verify generated filler configuration locally without cloud credentials:

```bash
server/venv/bin/python -m pytest -q server/tests
```

For an end-to-end check with an App ID that has an Engine generator provisioned,
set only:

```env
FILLER_WORDS_MODE=generated
```

Otherwise, set all three `FILLER_LLM_*` fields to a third-party public
OpenAI-compatible provider. Use ngrok or another HTTPS tunnel only when the
provider itself runs locally; Agora Engine cannot call `localhost`.

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
- The `/api/get_config` · `/api/startAgent` · `/api/stopAgent` contract between the web client and the backend (Next rewrites, no Route Handlers).
- **Managed keyless OpenAI** powering the assistant — Agora-managed, no `OPENAI_API_KEY` required.
- **filler_words** static phrase list by default, or Engine 2.12 generated phrases with static fallback when `FILLER_WORDS_MODE=generated`.
- **farewell_config** graceful exit: the agent speaks a farewell before leaving the channel.
- **Zero-key** setup — the full pipeline runs with no LLM API key by default.

## How It Works

1. The browser calls `/api/get_config`, which Next rewrites to the backend; the
   backend mints an Agora token from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
2. The browser joins the RTC channel, then calls `/api/startAgent`; the backend
   starts an agent session using the managed OpenAI vendor with `filler_words`
   and `farewell_config` configured.
3. The user speaks. Agora runs STT (Deepgram, nova-3) and produces a transcript.
4. While the LLM is generating a response, Agora either plays a randomly
   selected static phrase or asks the App ID's Engine-managed generator (or an
   optional BYO provider) for a short phrase. Generated mode falls back to the
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
| No filler phrases heard | Check that `filler_words.enable` is `true` and phrases list is non-empty in `server/src/filler_config.py`. |
| Generated mode does not start | Check that the App ID has the Engine generator enabled. For BYO, set all three `FILLER_LLM_*` fields and use a public `/chat/completions` endpoint. |
| No farewell on hang-up | Verify `farewell_config.graceful_enabled` is `true`; the agent needs a moment (`graceful_timeout_seconds`) to speak before it exits. |
| Local calls fail under a global proxy (Clash, etc.) | Configure your proxy to send `127.0.0.1`, `localhost`, and RFC-1918 ranges DIRECT. |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
