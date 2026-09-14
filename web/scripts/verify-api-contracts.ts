import { existsSync, readdirSync } from 'node:fs'
import path from 'node:path'

import nextConfig from '../next.config'
import { getConfig, getFillerConfig, startAgent, stopAgent } from '../src/services/api'

type Rewrite = {
  source: string
  destination: string
}

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message)
  }
}

async function getRewrites(): Promise<Rewrite[]> {
  const rewrites = nextConfig.rewrites
  assert(typeof rewrites === 'function', 'next.config.ts should define async rewrites()')

  const result = await rewrites()
  if (Array.isArray(result)) {
    return result as Rewrite[]
  }

  return [
    ...((result.beforeFiles ?? []) as Rewrite[]),
    ...((result.afterFiles ?? []) as Rewrite[]),
    ...((result.fallback ?? []) as Rewrite[]),
  ]
}

function requestUrl(input: Parameters<typeof fetch>[0]) {
  if (typeof input === 'string' || input instanceof URL) {
    return new URL(input, 'http://localhost:3000')
  }
  return new URL(input.url)
}

function getRequestBody(init: RequestInit | undefined) {
  assert(typeof init?.body === 'string', 'POST request should include a JSON string body')
  return JSON.parse(init.body) as Record<string, unknown>
}

async function verifyRewriteContract() {
  const originalBackendUrl = process.env.AGENT_BACKEND_URL
  process.env.AGENT_BACKEND_URL = 'http://localhost:8000/'

  try {
    const rewrites = await getRewrites()
    assert(
      rewrites.some(
        (rewrite) => rewrite.source === '/api/get_config' && rewrite.destination === 'http://localhost:8000/get_config',
      ),
      'next.config.ts should rewrite /api/get_config to /get_config on the Python backend',
    )
    assert(
      rewrites.some(
        (rewrite) => rewrite.source === '/api/filler_config' && rewrite.destination === 'http://localhost:8000/filler_config',
      ),
      'next.config.ts should rewrite /api/filler_config to /filler_config on the Python backend',
    )
    assert(
      rewrites.some(
        (rewrite) => rewrite.source === '/api/startAgent' && rewrite.destination === 'http://localhost:8000/startAgent',
      ),
      'next.config.ts should rewrite /api/startAgent to /startAgent on the Python backend',
    )
    assert(
      rewrites.some(
        (rewrite) => rewrite.source === '/api/stopAgent' && rewrite.destination === 'http://localhost:8000/stopAgent',
      ),
      'next.config.ts should rewrite /api/stopAgent to /stopAgent on the Python backend',
    )
  } finally {
    if (originalBackendUrl) {
      process.env.AGENT_BACKEND_URL = originalBackendUrl
    } else {
      process.env.AGENT_BACKEND_URL = ''
    }
  }
}

async function verifyRouteHandlersRemoved() {
  const apiDir = path.join(process.cwd(), 'app', 'api')
  if (!existsSync(apiDir)) {
    return
  }

  const pendingDirs = [apiDir]
  while (pendingDirs.length > 0) {
    const currentDir = pendingDirs.pop()
    assert(currentDir, 'Expected a directory to scan')

    for (const entry of readdirSync(currentDir, { withFileTypes: true })) {
      const entryPath = path.join(currentDir, entry.name)
      if (entry.isDirectory()) {
        pendingDirs.push(entryPath)
      }
      assert(!entryPath.endsWith(`${path.sep}route.ts`), `${entryPath} should not exist`)
    }
  }
}

async function verifyApiClientRequests() {
  const originalFetch = globalThis.fetch
  const seenPaths: string[] = []
  const seenModes: unknown[] = []

  globalThis.fetch = (async (input, init) => {
    const url = requestUrl(input)
    seenPaths.push(url.pathname)

    if (url.pathname === '/api/filler_config') {
      assert(init?.method === 'GET', 'GET /api/filler_config should use GET')
      assert(init?.cache === 'no-store', 'Default filler mode should be fetched without caching')
      return Response.json({ code: 0, data: { default_mode: 'generated' }, msg: 'success' })
    }

    if (url.pathname === '/api/get_config') {
      assert(init?.method === 'GET', 'GET /api/get_config should use GET')
      assert(url.searchParams.get('uid') === '1234', 'GET /api/get_config should pass the requested uid')
      assert(
        url.searchParams.get('channel') === 'test-channel',
        'GET /api/get_config should pass the requested channel',
      )

      return Response.json({
        code: 0,
        data: {
          app_id: 'stub-app-id',
          token: 'stub-token',
          uid: '1234',
          channel_name: 'test-channel',
          agent_uid: '9999',
        },
        msg: 'success',
      })
    }

    if (url.pathname === '/api/startAgent') {
      assert(init?.method === 'POST', 'POST /api/startAgent should use POST')
      const body = getRequestBody(init)
      assert(body.channelName === 'test-channel', 'POST /api/startAgent should include channelName')
      assert(body.rtcUid === 9999, 'POST /api/startAgent should include rtcUid')
      assert(body.userUid === 1234, 'POST /api/startAgent should include userUid')
      seenModes.push(body.fillerWordsMode)

      return Response.json({
        code: 0,
        data: {
          agent_id: 'mock-agent-id',
          channel_name: 'test-channel',
          status: 'started',
        },
        msg: 'success',
      })
    }

    if (url.pathname === '/api/stopAgent') {
      assert(init?.method === 'POST', 'POST /api/stopAgent should use POST')
      const body = getRequestBody(init)
      assert(body.agentId === 'mock-agent-id', 'POST /api/stopAgent should include agentId')
      return Response.json({ code: 0, msg: 'success' })
    }

    return Response.json({ detail: `Unexpected request path: ${url.pathname}` }, { status: 404 })
  }) as typeof fetch

  try {
    const fillerConfig = await getFillerConfig()
    assert(fillerConfig.default_mode === 'generated', 'Filler settings should preserve the backend default')

    const config = await getConfig({ uid: 1234, channel: 'test-channel' })
    assert(config.token === 'stub-token', 'GET /api/get_config should return response data')

    const agentId = await startAgent('test-channel', 9999, 1234)
    assert(agentId === 'mock-agent-id', 'POST /api/startAgent should return the agent id')

    await stopAgent(agentId)

    await startAgent('test-channel', 9999, 1234, 'static')
    await startAgent('test-channel', 9999, 1234, 'generated')
    assert(
      seenModes.length === 3 && seenModes[0] === undefined && seenModes[1] === 'static' && seenModes[2] === 'generated',
      'POST /api/startAgent should preserve omitted, static, and generated filler modes',
    )

    assert(
      JSON.stringify(seenPaths) === JSON.stringify([
        '/api/filler_config', '/api/get_config', '/api/startAgent', '/api/stopAgent', '/api/startAgent', '/api/startAgent',
      ]),
      'API client should call the unversioned /api paths',
    )
  } finally {
    globalThis.fetch = originalFetch
  }
}

async function main() {
  await verifyRewriteContract()
  await verifyRouteHandlersRemoved()
  await verifyApiClientRequests()
  console.log('API contract checks passed')
}

await main()
