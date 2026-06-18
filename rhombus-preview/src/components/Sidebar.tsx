import type { ContextFile, FileTreeNode } from '../types'
import { fileKey } from '../lib/registry'

interface SidebarProps {
  tree: FileTreeNode[]
  selectedKey: string | null
  onSelectFile: (file: ContextFile) => void
  width?: number
}

function FileButton({ file, label, selectedKey, onSelectFile, }: {
  file: ContextFile
  label: string
  selectedKey: string | null
  onSelectFile: (file: ContextFile) => void
}) {
  const key = fileKey(file)
  const selected = key === selectedKey

  return (
    <button
      className={`tree-node file ${selected ? 'is-selected' : ''}`}
      title={`${file.registry} · ${file.id}`}
      type="button"
      onClick={() => onSelectFile(file)}
    >
      <span className="tree-file-dot" />
      <span className="tree-node-label">{label.replace(/\.json$/i, '')}</span>
    </button>
  )
}

function Chevron() {
  return (
    <svg className="tree-chevron" width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6 4L10 8L6 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

function renderNode(node: FileTreeNode, selectedKey: string | null, onSelectFile: (file: ContextFile) => void) {
  if (node.kind === 'file' && node.file) {
    return <FileButton key={node.key} file={node.file} label={node.label} selectedKey={selectedKey} onSelectFile={onSelectFile} />
  }

  const isRegistry = node.kind === 'registry'
  const isCollapsable = !isRegistry
  const classes = `tree-node ${isCollapsable ? 'collapsable' : ''}`.trim()

  return (
    <details key={node.key} className={classes} open>
      <summary 
        onClick={isRegistry ? (e) => e.preventDefault() : undefined}
        style={isRegistry ? { cursor: 'default' } : undefined}
      >
        {isCollapsable && <Chevron />}
        {node.label}
      </summary>
      <div className="tree-children">
        {node.children?.map((child) => renderNode(child, selectedKey, onSelectFile))}
      </div>
    </details>
  )
}

export default function Sidebar({ tree, selectedKey, onSelectFile, width }: SidebarProps) {
  return (
    <aside className="sidebar" style={{ width: width ? `${width}px` : undefined, flex: width ? 'none' : undefined }}>
      <div className="sidebar-header">
        <div className="sidebar-title">Rhombus Preview</div>
        <div className="sidebar-subtitle">Context files</div>
      </div>
      <div className="sidebar-content">
        {tree.length === 0 ? <div className="sidebar-empty">No files loaded.</div> : tree.map((node) => renderNode(node, selectedKey, onSelectFile))}
      </div>
    </aside>
  )
}
