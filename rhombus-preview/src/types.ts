/** Interface for the file objects how they are provided by the Rhombus service endpoint. */
export interface RhombusContextFile {
  registry: string
  id: string
  content: unknown
  language: string
}

export interface RegistrySection {
  registry: string
  title: string
  files: RhombusContextFile[]
}

export interface SidebarFileEntry {
  file: RhombusContextFile
  key: string
  namespace: string
  pathParts: string[]
  displayName: string
}

export interface FileTreeNode {
  key: string
  label: string
  kind: 'registry' | 'namespace' | 'folder' | 'file'
  file?: RhombusContextFile
  children?: FileTreeNode[]
}

export interface RhombusExtensionAPI {
  React: any;
  deepslate: any;
  densityFunctions: Map<string, (obj: any, inputParser: any) => any>;
  visualizers: Map<string, React.FC<any>>;
}

declare global {
  interface Window {
    rhombus: RhombusExtensionAPI;
  }
}
