import type { RhombusContextFile } from '../types'

/**
 * Formats the given base endpoint URL into the events endpoint URL for Server-Sent Events.
 */
export function getEventsEndpoint(endpoint: string): string {
  return `${endpoint.replace(/\/+$/, '')}/events`
}

/**
 * Fetches the latest JSON context files from the given backend endpoint.
 * Throws an error if the request fails or the payload is malformed.
 */
export async function loadContextFiles(endpoint: string): Promise<RhombusContextFile[]> {
  const url = `${endpoint.replace(/\/+$/, '')}/data?t=${Date.now()}`
  const response = await fetch(url, {
    cache: 'no-store',
    headers: {
      Accept: 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Endpoint ${endpoint} replied with ${response.status} ${response.statusText}`)
  }

  const payload = (await response.json()) as unknown
  const files = payload && typeof payload === 'object' ? (payload as any).latest_data : null

  if (!Array.isArray(files)) {
    throw new Error('The endpoint must return an object with a "latest_data" array.')
  }

  return files.map((entry, index) => {
    if (!entry || typeof entry !== 'object') {
      throw new Error(`File entry at index ${index} is not an object.`)
    }

    const file = entry as Record<string, unknown>
    const registry = file.registry
    const id = file.id
    const content = file.content

    if (typeof registry !== 'string' || typeof id !== 'string') {
      throw new Error(`File entry at index ${index} must contain string fields registry and id.`)
    }

    return {
      registry,
      id,
      content,
    }
  })
}
