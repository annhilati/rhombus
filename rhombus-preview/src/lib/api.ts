import type { ContextFile } from '../types'

const DEFAULT_ENDPOINT = (import.meta.env.VITE_CONTEXT_ENDPOINT as string | undefined) ?? '/data'

export function getContextEndpoint(): string {
  return DEFAULT_ENDPOINT
}

export async function loadContextFiles(endpoint = DEFAULT_ENDPOINT): Promise<ContextFile[]> {
  const response = await fetch(endpoint, {
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
