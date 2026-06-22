import type { RhombusContextFile, FileTreeNode } from '../types'
import { normalizeRegistryName, parseFileId, prettyRegistryTitle } from './registry'

/**
 * Compares two FileTreeNodes for sorting purposes.
 * Orders nodes hierarchically: Registries -> Namespaces -> Folders -> Files, and falls back to alphabetical order.
 */
function compareNodes(a: FileTreeNode, b: FileTreeNode): number {
  const rank = { registry: 0, namespace: 1, folder: 2, file: 3 } as const
  const delta = rank[a.kind] - rank[b.kind]
  if (delta !== 0) return delta
  return a.label.localeCompare(b.label)
}

/**
 * Recursively inserts a file into the nested tree structure based on its parsed path segments.
 * Mutates the provided children array.
 */
function insertPath(children: FileTreeNode[], parts: string[], file: RhombusContextFile, keyPrefix: string): void {
  if (parts.length === 0) {
    const existing = children.find((entry) => entry.kind === 'file' && entry.file && entry.file.id === file.id)
    if (!existing) {
      children.push({
        key: `${keyPrefix}::${file.id}`,
        label: parseFileId(file.id).displayName,
        kind: 'file',
        file,
      })
    }
    return
  }

  const [head, ...tail] = parts
  const isLeaf = tail.length === 0

  let node = children.find((entry) => entry.kind === (isLeaf ? 'file' : 'folder') && entry.label === head)
  if (!node) {
    node = isLeaf
      ? {
          key: `${keyPrefix}::${head}`,
          label: head,
          kind: 'file',
          file,
        }
      : {
          key: `${keyPrefix}::${head}`,
          label: head,
          kind: 'folder',
          children: [],
        }
    children.push(node)
  }

  if (node.kind === 'file') return

  if (isLeaf) {
    node.children ??= []
    node.children.push({
      key: `${keyPrefix}::${file.id}`,
      label: head,
      kind: 'file',
      file,
    })
    return
  }

  node.children ??= []
  insertPath(node.children, tail, file, keyPrefix)
}

/**
 * Takes a flat list of RhombusContextFiles and constructs a fully nested hierarchical tree suitable for the Sidebar UI.
 * The tree is structured by Registry -> Namespace -> Folders... -> File.
 */
export function buildTree(files: RhombusContextFile[]): FileTreeNode[] {
  const registries = new Map<string, FileTreeNode>()

  for (const file of files) {
    const registry = normalizeRegistryName(file.registry)
    const { namespace, pathParts, displayName } = parseFileId(file.id)

    let registryNode = registries.get(registry)
    if (!registryNode) {
      registryNode = {
        key: registry,
        label: prettyRegistryTitle(registry),
        kind: 'registry',
        children: [],
      }
      registries.set(registry, registryNode)
    }

    let namespaceNode = registryNode.children!.find((entry) => entry.kind === 'namespace' && entry.label === namespace)
    if (!namespaceNode) {
      namespaceNode = {
        key: `${registry}::${namespace}`,
        label: namespace,
        kind: 'namespace',
        children: [],
      }
      registryNode.children!.push(namespaceNode)
    }

    const leafParts = [...pathParts]
    if (leafParts.length === 0) leafParts.push(displayName)

    insertPath(namespaceNode.children!, leafParts, file, `${registry}::${namespace}`)
  }

  const sortedRegistries = [...registries.values()].sort((a, b) => a.label.localeCompare(b.label))
  for (const registryNode of sortedRegistries) {
    const visit = (node: FileTreeNode) => {
      if (node.children) {
        node.children.sort(compareNodes)
        for (const child of node.children) visit(child)
      }
    }
    visit(registryNode)
  }

  return sortedRegistries
}
