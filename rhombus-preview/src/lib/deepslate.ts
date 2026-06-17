import { Identifier, Registry } from 'deepslate'
import type { ContextFile } from '../types'

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
        const data = filesByRegistry.get(key.path) ?? {}
        Object.entries(data).forEach(([type, value]) => {
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
