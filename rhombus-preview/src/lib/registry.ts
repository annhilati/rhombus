import type { ContextFile, RegistrySection, VisualizationKind } from '../types'

export function normalizeRegistryName(raw: string): string {
  const lower = raw.trim().toLowerCase()
  if (lower === 'worldgen/noise' || lower === 'minecraft:noise' || lower === 'noise') {
    return 'minecraft:noise'
  }
  if (
    lower === 'worldgen/density_function' ||
    lower === 'minecraft:density_function' ||
    lower === 'density_function' ||
    lower === 'density-function'
  ) {
    return 'minecraft:density_function'
  }
  return raw
}

export function prettyRegistryTitle(raw: string): string {
  const normalized = normalizeRegistryName(raw)
  if (normalized === 'minecraft:noise') return 'minecraft:noise'
  if (normalized === 'minecraft:density_function') return 'minecraft:density_function'
  return raw
}

export function getVisualizationKind(registry: string): VisualizationKind {
  const normalized = normalizeRegistryName(registry)
  if (normalized === 'minecraft:noise') return 'noise'
  if (normalized === 'minecraft:density_function') return 'density_function'
  return null
}

export function fileKey(file: ContextFile): string {
  return `${normalizeRegistryName(file.registry)}::${file.id}`
}

export function parseFileId(id: string): { namespace: string; path: string; pathParts: string[]; displayName: string } {
  const trimmed = id.trim()
  const colonIndex = trimmed.indexOf(':')
  const namespace = colonIndex >= 0 ? trimmed.slice(0, colonIndex) || 'minecraft' : 'minecraft'
  const path = colonIndex >= 0 ? trimmed.slice(colonIndex + 1) : trimmed
  const cleaned = path.replace(/\.json$/i, '')
  const pathParts = cleaned.split('/').filter(Boolean)
  const displayName = pathParts.at(-1) ?? (cleaned || namespace)
  return { namespace, path: cleaned, pathParts, displayName }
}

export function groupByRegistry(files: ContextFile[]): RegistrySection[] {
  const map = new Map<string, ContextFile[]>()

  for (const file of files) {
    const key = normalizeRegistryName(file.registry)
    const bucket = map.get(key)
    if (bucket) bucket.push(file)
    else map.set(key, [file])
  }

  return [...map.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([registry, bucket]) => ({
      registry,
      title: prettyRegistryTitle(registry),
      files: bucket.slice().sort((a, b) => a.id.localeCompare(b.id)),
    }))
}
