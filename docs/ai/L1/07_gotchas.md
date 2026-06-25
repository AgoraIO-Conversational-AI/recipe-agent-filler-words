# 07 · Gotchas

> Non-obvious pitfalls specific to the filler-words recipe. Read before changing the agent, filler config, env, or verify scripts.

## Filler-words mode must stay `"static"`

SDK 2.0.0 supports `mode: "static"` only. Do **not** set `mode: "llm"` or any other value — the Agora cloud will reject it. Edit only the `phrases` list and `selection_rule` in `filler_config.py`.

## `OPENAI_API_KEY` is optional, not required

Unlike the realtime recipe, `OPENAI_API_KEY` is **optional** here. Agora manages the OpenAI key by default. Only set it if your account requires a BYO key. The server boots and runs without it.

## Agora credentials are required at boot

`Agent.__init__` raises `ValueError` immediately if `AGORA_APP_ID` or `AGORA_APP_CERTIFICATE` are missing. The server sets `agent = None` on this failure and returns 500 on all routes. Set both before starting.

## Do not put `PORT` in `server/.env.example`

`verify:local:fastapi` injects a random `PORT` and loads env with `load_dotenv(override=True)`. A `PORT` line in `.env.example` (copied to `.env.local`) would clobber the injected port and break the smoke test.

## Keep `/api/*` ownership in rewrites

Adding `web/app/api/**/route.ts` for agent/token logic breaks the boundary — `verify-api-contracts.ts` explicitly fails if a `route.ts` exists under `app/api`. Token logic belongs in `server/`.

## camelCase request fields

`StartAgentRequest` uses `channelName`, `rtcUid`, `userUid` (camelCase) to match the browser client. Renaming one side without the other breaks the contract tests.

## UID normalization in transcripts

`normalizeTranscript` maps `uid === '0'` to the local UID. Token issuance also rejects zero/negative UIDs and generates a concrete one. Preserve both — speaker mapping and tokens depend on concrete UIDs.

## `farewell_config` lives in `parameters`, not as a top-level arg

`farewell_config` is embedded inside the `parameters` dict passed to `AgoraAgent(...)`. It is **not** a direct keyword argument to `AgoraAgent`. Placing it at the wrong level will silently have no effect.

## Local calls under a global proxy

Global proxies (Clash, etc.) can break `localhost`/RFC-1918 traffic. Configure the proxy to send `127.0.0.1`, `localhost`, and private ranges DIRECT, or use `socksio` (in `requirements.txt`) plus `all_proxy` to route through SOCKS.

## Related Deep Dives

- [filler_words_config](L2/filler_words_config.md) — correct filler/VAD/farewell wiring.
