# recipe-agent-filler-words — Repo Card

> Next.js web client + Python FastAPI backend for an Agora Conversational AI voice agent that plays natural filler phrases during LLM latency and exits gracefully. Pipeline: DeepgramSTT → managed OpenAI → MiniMaxTTS. Zero-key by default.

## Identity

| Field          | Value                                                                        |
| -------------- | ---------------------------------------------------------------------------- |
| Repo           | `AgoraIO-Conversational-AI/recipe-agent-filler-words`                        |
| Type           | `distributed-system` (single repo, two co-located processes)                 |
| Language       | Python 3.10+ (FastAPI + uvicorn) backend + Next.js 16 / React 19 web         |
| Deploy Target  | `web/` as Next.js app, `server/` as a reachable FastAPI service              |
| Owner          | Agora Conversational AI DevEx                                                |
| Last Reviewed  | 2026-06-25                                                                   |
| Recipe Role    | `base`                                                                       |
| Recipe Version | `1.0.0`                                                                      |
| Recipe Status  | `experimental`                                                               |

## L1 — Summaries

The Audience column helps agents prioritise: **Use** = consuming the recipe's behavior, **Maintain** = modifying internals.

| File                                     | Purpose                                                                              | Audience       |
| ---------------------------------------- | ------------------------------------------------------------------------------------ | -------------- |
| [01_setup](L1/01_setup.md)               | bun + venv + pip setup, env vars (zero-key: only `AGORA_APP_ID/CERTIFICATE` required), commands | Use & Maintain |
| [02_architecture](L1/02_architecture.md) | Two-process topology, filler-words/farewell mechanism, cascading pipeline lifecycle  | Maintain       |
| [03_code_map](L1/03_code_map.md)         | `web/` and `server/` trees with key file responsibilities                            | Maintain       |
| [04_conventions](L1/04_conventions.md)   | Python async + FastAPI patterns, Biome, JSON envelope, cascading vendor wiring       | Maintain       |
| [05_workflows](L1/05_workflows.md)       | Add a route, change filler phrases/model/voice, adjust VAD, verify, deploy           | Use            |
| [06_interfaces](L1/06_interfaces.md)     | FastAPI route contracts, rewrites, env vars, filler/farewell config shapes           | Use & Maintain |
| [07_gotchas](L1/07_gotchas.md)           | Static-only filler mode, PORT env, OPENAI_API_KEY optional, camelCase fields         | Maintain       |
| [08_security](L1/08_security.md)         | Token007, App Certificate server-only, CORS, zero-key OpenAI, codec                 | Maintain       |

## Recipe Profile

This repo declares `Recipe Role: base`. See [RECIPE.md](RECIPE.md) for extension points, invariants, and stable contracts before changing reusable surfaces.
