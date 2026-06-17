import type { ContextFile, TreeNode } from '../types'
import { fileKey } from '../lib/registry'

interface SidebarProps {
  tree: TreeNode[]
  selectedKey: string | null
  onSelectFile: (file: ContextFile) => void
}

function FileButton({
  file,
  selectedKey,
  onSelectFile,
}: {
  file: ContextFile
  selectedKey: string | null
  onSelectFile: (file: ContextFile) => void
}) {
  const key = fileKey(file)
  const selected = key === selectedKey

  return (
    <button
      type="button"
      className={`tree-leaf ${selected ? 'is-selected' : ''}`}
      onClick={() => onSelectFile(file)}
      title={`${file.registry} · ${file.id}`}
    >
      <span className="tree-leaf-dot" />
      <span className="tree-leaf-label">{file.id.replace(/\.json$/i, '')}</span>
    </button>
  )
}

function renderNode(node: TreeNode, selectedKey: string | null, onSelectFile: (file: ContextFile) => void) {
  if (node.kind === 'file' && node.file) {
    return <FileButton file={node.file} selectedKey={selectedKey} onSelectFile={onSelectFile} />
  }

  const open = node.kind === 'registry'
  return (
    <details className={`tree-node tree-${node.kind}`} open={open}>
      <summary>{node.label}</summary>
      <div className="tree-children">
        {node.children?.map((child) => (
          <div key={child.key}>{renderNode(child, selectedKey, onSelectFile)}</div>
        ))}
      </div>
    </details>
  )
}

export default function Sidebar({ tree, selectedKey, onSelectFile }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">Rhombus Preview</div>
        <div className="sidebar-subtitle">Context files</div>
      </div>
      <div className="sidebar-content">
        {tree.length === 0 ? <div className="sidebar-empty">No files loaded.</div> : tree.map((node) => <div key={node.key}>{renderNode(node, selectedKey, onSelectFile)}</div>)}
      </div>
    </aside>
  )
}
