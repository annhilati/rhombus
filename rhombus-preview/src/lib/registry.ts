import type { RhombusContextFile, RegistrySection } from '../types'

/**
 * Normalizes a registry name so it does not include a namespace. Example: `"worldgen/density_function"`
 */
export function normalizeRegistryName(raw: string): string {
  const lower = raw.trim().toLowerCase()
  
  const colonIndex = lower.indexOf(':')
  if (colonIndex >= 0) {
    return lower.slice(colonIndex + 1)
  }
  return lower
}

/**
 * Converts a raw registry name into a human-readable title (e.g., "density_function" becomes "DENSITY FUNCTION").
 */
export function prettyRegistryTitle(raw: string): string {
  const normalized = normalizeRegistryName(raw)
  return normalized.replace(/[_/-]/g, ' ').toUpperCase()
}

/**
 * Generates a unique key for a file based on its normalized registry name and ID.
 */
export function fileKey(file: RhombusContextFile): string {
  return `${normalizeRegistryName(file.registry)}::${file.id}`
}

/**
 * Parses a standard Minecraft file ID (like `"minecraft:my/path/file"`) into its structural components.
 */
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

/**
 * Groups a flat array of Rhombus context files into sections categorized and sorted by their registry names.
 */
export function groupByRegistry(files: RhombusContextFile[]): RegistrySection[] {
  const map = new Map<string, RhombusContextFile[]>()

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
