import { Identifier, Registry } from 'deepslate'
import type { ContextFile } from '../types'

let vanillaCache: Record<string, Record<string, any>> | null = null

export async function fetchVanillaData(): Promise<void> {
  if (vanillaCache) return

  const urls = {
    'worldgen/noise': 'https://raw.githubusercontent.com/misode/mcmeta/summary/data/worldgen/noise/data.min.json',
    'worldgen/density_function': 'https://raw.githubusercontent.com/misode/mcmeta/summary/data/worldgen/density_function/data.min.json'
  }

  const cache: Record<string, Record<string, any>> = {
    'worldgen/noise': {},
    'worldgen/density_function': {}
  }

  await Promise.all(Object.entries(urls).map(async ([registry, url]) => {
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.statusText}`)
    const data = await res.json()
    cache[registry] = data
  }))

  vanillaCache = cache
}

export interface DeepslateRuntime {
  registerAllFiles: (files: ContextFile[]) => void
}

export function loadDeepslateRuntime(): DeepslateRuntime {
  return {
    registerAllFiles(files: ContextFile[]) {
      // Group files by registry
      const filesByRegistry = new Map<string, Record<string, string>>()
      for (const file of files) {
        if (!filesByRegistry.has(file.registry)) {
          filesByRegistry.set(file.registry, {})
        }
        filesByRegistry.get(file.registry)![file.id] = JSON.stringify(file.content)
      }

      // Populate deepslate registries
      Registry.REGISTRY.forEach((key, registry) => {
        registry.clear()
        const userData = filesByRegistry.get(key.path) ?? {}
        
        const userOverrides = new Set<string>()
        Object.keys(userData).forEach(k => {
          try {
            userOverrides.add(Identifier.parse(k).toString())
          } catch {}
        })

        // 1. Register Vanilla data
        if (vanillaCache && vanillaCache[key.path]) {
          const vData = vanillaCache[key.path]
          Object.entries(vData).forEach(([type, value]) => {
            try {
              const parsedId = Identifier.parse(type)
              if (!userOverrides.has(parsedId.toString())) {
                registry.register(parsedId, registry.parse(value))
              }
            } catch (e) {
              console.warn(`Failed to parse vanilla ${key.path} ${type}`, e)
            }
          })
        }

        // 2. Register user data
        Object.entries(userData).forEach(([type, value]) => {
          try {
            registry.register(Identifier.parse(type), registry.parse(JSON.parse(value)))
          } catch (e) {
            console.warn(`Failed to parse ${key.path} ${type}`, e)
          }
        })
      })
    },
  }
}
