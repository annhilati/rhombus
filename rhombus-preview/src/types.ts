export interface ContextFile {
  registry: string
  id: string
  content: unknown
}

export type VisualizationKind = 'noise' | 'density_function' | null

export interface RegistrySection {
  registry: string
  title: string
  files: ContextFile[]
}

export interface SidebarFileEntry {
  file: ContextFile
  key: string
  namespace: string
  pathParts: string[]
  displayName: string
}

export interface FileTreeNode {
  key: string
  label: string
  kind: 'registry' | 'namespace' | 'folder' | 'file'
  file?: ContextFile
  children?: FileTreeNode[]
}
