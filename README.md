# Agora Conversational AI — Filler Words Recipe (Python)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Bun](https://img.shields.io/badge/bun-latest-black)](https://bun.sh/)

The **filler words** recipe in the Agora Conversational AI recipes family.
A friendly voice agent that plays natural filler phrases during LLM latency
gaps and says a graceful goodbye when the conversation ends. Fully **zero-key**
— OpenAI is Agora-managed (no `OPENAI_API_KEY` required unless you bring your
own account).

**Pipeline:** `DeepgramSTT(nova-3)` → `OpenAI` (friendly assistant) → `MiniMaxTTS`

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Bun](https://bun.sh/)
- [Agora CLI](https://github.com/AgoraIO/cli) — makes generating an App ID + App Certificate easy

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
- Mock LLM — N/A (managed OpenAI, no local service)
- API docs — http://localhost:8000/docs

## Deploy

Deploy `web` (Next.js) and `server` (a reachable FastAPI backend). Set
`AGENT_BACKEND_URL` in the web deployment so the Next rewrites reach the backend.

A backend-only Docker image is published to
`ghcr.io/AgoraIO-Conversational-AI/recipe-agent-filler-words` on `v*` tags.
It exposes **BACKEND-ONLY** (:8000). No separate LLM container is needed —
OpenAI is Agora-managed.

## Environment variables

Backend env file: [`server/.env.example`](server/.env.example).

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | yes | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | yes | — | Agora Console → Project → App Certificate |
| `OPENAI_MODEL` | | `gpt-4o-mini` | OpenAI model for the assistant |
| `OPENAI_API_KEY` | | — | Optional — Agora manages the OpenAI key by default (keyless). Set only if your account requires it. |
| `TTS_VOICE` | | `English_captivating_female1` | MiniMax TTS voice |
| `AGENT_GREETING` | | built-in | Optional opening line override |

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

## Architecture

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session (managed OpenAI vendor)
                          │  filler_words: static phrases during LLM latency
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
- **filler_words** static phrase list played during LLM latency (SDK 2.0.0 supports `mode: "static"` only).
- **farewell_config** graceful exit: the agent speaks a farewell before leaving the channel.
- **Zero-key** setup — the full pipeline runs with no LLM API key by default.

## How It Works

1. The browser calls `/api/get_config`, which Next rewrites to the backend; the
   backend mints an Agora token from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
2. The browser joins the RTC channel, then calls `/api/startAgent`; the backend
   starts an agent session using the managed OpenAI vendor with `filler_words`
   and `farewell_config` configured.
3. The user speaks. Agora runs STT (Deepgram, nova-3) and produces a transcript.
4. While the LLM is generating a response, Agora plays a randomly selected
   filler phrase from the static list, masking the silence.
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
| No farewell on hang-up | Verify `farewell_config.graceful_enabled` is `true`; the agent needs a moment (`graceful_timeout_seconds`) to speak before it exits. |
| Local calls fail under a global proxy (Clash, etc.) | Configure your proxy to send `127.0.0.1`, `localhost`, and RFC-1918 ranges DIRECT. |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
