# 06 · Interfaces

> Boundary contracts: backend routes, the `/api/*` rewrite map, env vars, the response envelope, and the filler-words/farewell config shapes.

## Backend routes (port 8000)

The browser calls these as `/api/<name>`; Next rewrites to the backend `/<name>`.

### `GET /get_config`

- Query (optional): `channel?: string`, `uid?: int` (≤ 0 or missing → backend generates one).
- Returns `data`: `{ app_id, token, uid (string), channel_name, agent_uid (string) }`.
- Token is a Token007 RTC+RTM token, expiry 3600s, for a concrete non-zero UID.

### `POST /startAgent`

- Body: `{ channelName: string, rtcUid: int, userUid: int, parameters?: object }`.
  - `parameters.output_audio_codec?: string` is the only honored parameter field.
- Returns `data`: `{ agent_id, channel_name, status: "started" }`.
- 400 if `channelName`/`rtcUid`/`userUid` invalid. 500 if `AGORA_APP_ID`/`AGORA_APP_CERTIFICATE` unset at boot.

### `POST /stopAgent`

- Body: `{ agentId: string }`.
- Returns `{ code: 0, msg: "success" }` (no `data`).

## Response envelope

```json
{ "code": 0, "msg": "success", "data": { } }
```

`data` omitted when the route has no payload. Non-zero `code` or missing `data` = error on the client side.

## Rewrite map (`web/next.config.ts`)

| Browser path        | Backend destination |
| ------------------- | ------------------- |
| `/api/get_config`   | `/get_config`       |
| `/api/startAgent`   | `/startAgent`       |
| `/api/stopAgent`    | `/stopAgent`        |

`rewrites()` returns `[]` when `AGENT_BACKEND_URL` is unset. The contract is asserted by `verify-api-contracts.ts` and exercised by `verify-local-proxy.ts`.

## Browser API client (`web/src/services/api.ts`)

- `getConfig({ channel?, uid? }) → GetConfigResponse`
- `startAgent(channelName, rtcUid, userUid) → agent_id`
- `stopAgent(agentId) → void`

## Environment variables

| Variable                | Scope          | Required | Default                         |
| ----------------------- | -------------- | :------: | ------------------------------- |
| `AGORA_APP_ID`          | backend        |    ✅    | —                               |
| `AGORA_APP_CERTIFICATE` | backend        |    ✅    | —                               |
| `OPENAI_MODEL`          | backend        |          | `gpt-4o-mini`                   |
| `OPENAI_API_KEY`        | backend        |          | — (Agora-managed if unset)      |
| `TTS_VOICE`             | backend        |          | `English_captivating_female1`   |
| `AGENT_GREETING`        | backend        |          | built-in line                   |
| `AGENT_BACKEND_URL`     | web (deploy)   |    ✅\*  | `http://localhost:8000` (dev)   |
| `PORT`                  | backend (env only) |      | `8000` — do **not** put in `.env.example` |

\* Required wherever the web app is deployed; rewrites are empty without it.

## Filler-words config shape (`filler_config.py`)

`build_filler_words()` returns the dict passed as `filler_words=` to `AgoraAgent(...)`:

```json
{
  "enable": true,
  "content": {
    "mode": "static",
    "static_config": {
      "phrases": ["Let me think about that for a second.", "..."],
      "selection_rule": "shuffle"
    }
  }
}
```

SDK 2.0.0 supports `mode: "static"` only.

## Farewell config shape (`filler_config.py`)

`build_farewell()` returns the dict embedded in `parameters["farewell_config"]`:

```json
{ "graceful_enabled": true, "graceful_timeout_seconds": 5 }
```

## Related Deep Dives

- [filler_words_config](L2/filler_words_config.md) — full VAD wiring and session parameter detail.
