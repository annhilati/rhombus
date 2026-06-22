import { Identifier, Registry } from 'deepslate'
import type { RhombusContextFile } from '../types'

let vanillaCache: Record<string, Record<string, any>> | null = null

/**
 * Fetches vanilla noise and density function data from the Misode repository and caches it in memory.
 * This ensures that built-in Minecraft resources are available when previewing files.
 */
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
  registerAllFiles: (files: RhombusContextFile[]) => void
}

/**
 * Initializes and returns a Deepslate runtime object.
 * The runtime provides a method to register custom JSON files alongside the cached vanilla data,
 * allowing Deepslate to sample blocks using those rules.
 */
export function loadDeepslateRuntime(): DeepslateRuntime {
  return {
    registerAllFiles(files: RhombusContextFile[]) {
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
