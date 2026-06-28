import { Identifier, Registry, DensityFunction } from 'deepslate'
import type { RhombusContextFile } from '../types'
import { patchState } from './deepslate-patch'

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

/**
 * Interface representing the Deepslate runtime environment.
 * It holds any parse errors and provides a method to register new files into registries.
 */
export interface DeepslateRuntime {
  /** A list of errors encountered during parsing or validation, tagged by the file ID */
  parseErrors: {fileId: string, error: string}[]
  /** Clears the registries and registers the given files, logging any parse errors. */
  registerFiles: (files: RhombusContextFile[]) => void
}

/**
 * Initializes and returns a Deepslate runtime object.
 * The runtime provides a method to register custom JSON files alongside the cached vanilla data,
 * allowing Deepslate to sample blocks using those rules.
 */
export function loadDeepslateRuntime(): DeepslateRuntime {
  return {
    parseErrors: [],
    registerFiles(files: RhombusContextFile[]) {
      this.parseErrors = [];
      patchState.errors = [];
      
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
        const lookupKey = key.namespace === 'minecraft' ? key.path : `${key.namespace}/${key.path}`;
        const userData = filesByRegistry.get(lookupKey) ?? {}
        
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
            patchState.currentFile = type;
            registry.register(Identifier.parse(type), registry.parse(JSON.parse(value)))
          } catch (e) {
            console.warn(`Failed to parse ${key.path} ${type}`, e)
            this.parseErrors.push({ fileId: type, error: e instanceof Error ? e.message : String(e) })
          } finally {
            patchState.currentFile = null;
          }
        })

        // 3. Validate references for user data (catches missing dependencies)
        Object.keys(userData).forEach(type => {
          try {
            const parsedId = Identifier.parse(type);
            const obj = registry.get(parsedId);
            if (obj) {
              const refsErrors = validateReferences(obj);
              refsErrors.forEach(err => {
                this.parseErrors.push({ fileId: type, error: err });
              });
            }
          } catch (e) {
            console.warn(`Failed to validate references for ${key.path} ${type}`, e)
          }
        });
      })

      // Add non-aborting parse errors (like unknown types) from the monkey-patch
      this.parseErrors.push(...patchState.errors);
    },
  }
}

/**
 * Generically crawls a parsed object (like a DensityFunction tree) to find unresolved Holders.
 * Calling obj.value() on an unresolved deepslate Holder throws a "Missing key in..." error,
 * which this function catches and collects. This completely avoids hardcoding registry names.
 */
export function validateReferences(obj: any, visited = new Set<any>()): string[] {
    if (!obj || typeof obj !== 'object') return [];
    if (visited.has(obj)) return [];
    visited.add(obj);

    const errors: string[] = [];

    // Identify deepslate Holders by their shape, and force them to resolve
    if (typeof obj.value === 'function' && typeof obj.key === 'function') {
        try {
            obj.value();
        } catch (e: any) {
            if (e instanceof Error && e.message.startsWith('Missing key in')) {
                errors.push(e.message);
            }
        }
    }

    // Traverse recursively
    for (const key in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, key)) {
            errors.push(...validateReferences(obj[key], visited));
        }
    }
    
    return errors;
}
