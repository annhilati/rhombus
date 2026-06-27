import { useState } from 'react'
import type { RhombusContextFile, FileTreeNode } from '../types'
import { fileKey } from '../lib/registry'

interface SidebarProps {
  tree: FileTreeNode[]
  selectedKey: string | null
  onSelectFile: (file: RhombusContextFile, newTab: boolean) => void
  endpoint: string
  onChangeEndpoint: (endpoint: string) => void
  width?: number
}

function getFileIconPath(file: RhombusContextFile): string {
  // Rangliste an Regex-Ausdrücken für Datei-Icons
  const rules = [
    { pattern: /density/i, icon: 'object' },
    { pattern: /noise/i, icon: 'object' },
    // Default fallback
    { pattern: /.*/, icon: 'object' }
  ];

  for (const rule of rules) {
    if (rule.pattern.test(file.id)) {
      return `/icons/${rule.icon}.svg`;
    }
  }
  return '/icons/object.svg';
}

/**
 * A selectable button representing a single file in the file tree.
 */
function FileButton({ file, label, selectedKey, onSelectFile, depth }: {
  file: RhombusContextFile
  label: string
  selectedKey: string | null
  onSelectFile: (file: RhombusContextFile, newTab: boolean) => void
  depth: number
}) {
  const key = fileKey(file)
  const selected = key === selectedKey

  return (
    <button
      style={{ paddingLeft: `${depth * 16}px` }}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.effectAllowed = 'copy';
        e.dataTransfer.setData('text/plain', key);
        (window as any).__draggedRhombusFile = file;
        (window as any).__draggedRhombusTabId = key + '-' + Date.now();
      }}
      onDragEnd={() => {
        (window as any).__draggedRhombusFile = null;
        (window as any).__draggedRhombusTabId = null;
      }}
      className={`tree-node file ${selected ? 'is-selected' : ''}`}
      title={`${file.registry} · ${file.id}`}
      type="button"
      onClick={(e) => onSelectFile(file, e.ctrlKey || e.metaKey)}
    >
      <img src={getFileIconPath(file)} className="tree-file-icon" alt="file" />
      <span className="tree-node-label">{label.replace(/\.json$/i, '')}</span>
    </button>
  )
}

/**
 * Renders the correct folder or namespace icon with open/closed state.
 */
function NodeIcon({ kind }: { kind: 'namespace' | 'folder' }) {
  return (
    <div className="tree-icon-wrapper">
      <img src={`/icons/${kind}.svg`} className="tree-icon-closed" alt={kind} />
      <img src={`/icons/${kind}_open.svg`} className="tree-icon-open" alt={`${kind} open`} />
    </div>
  )
}

/**
 * Recursively renders a node in the file tree (either a collapsible directory/registry or a file button).
 */
function TreeNode({ node, selectedKey, onSelectFile, depth = 0 }: {
  node: FileTreeNode
  selectedKey: string | null
  onSelectFile: (file: RhombusContextFile, newTab: boolean) => void
  depth?: number
}) {
  const [isOpen, setIsOpen] = useState(true)

  if (node.kind === 'file' && node.file) {
    return <FileButton file={node.file} label={node.label} selectedKey={selectedKey} onSelectFile={onSelectFile} depth={depth} />
  }

  const isRegistry = node.kind === 'registry'
  const isCollapsable = !isRegistry
  const classes = `tree-node ${isCollapsable ? 'collapsable' : ''} ${isRegistry ? 'registry' : ''}`.trim()

  return (
    <details 
      className={classes} 
      open={isRegistry ? true : isOpen}
      onToggle={isRegistry ? undefined : (e) => setIsOpen(e.currentTarget.open)}
    >
      <summary 
        onClick={isRegistry ? (e) => e.preventDefault() : undefined}
        style={{
          cursor: isRegistry ? 'default' : undefined,
          paddingLeft: isRegistry ? '7px' : `${depth * 16}px`
        }}
      >
        {isCollapsable && <NodeIcon kind={node.kind as 'namespace' | 'folder'} />}
        {node.label}
      </summary>
      <div className="tree-node-children">
        {node.children?.map((child) => (
          <TreeNode key={child.key} node={child} selectedKey={selectedKey} onSelectFile={onSelectFile} depth={depth + 1} />
        ))}
      </div>
    </details>
  )
}

/**
 * Renders the sidebar containing the file tree navigation and backend endpoint configuration.
 */
export default function Sidebar({ tree, selectedKey, onSelectFile, endpoint, onChangeEndpoint, width }: SidebarProps) {
  return (
    <aside className="sidebar" style={{ width: width ? `${width}px` : undefined, flex: width ? 'none' : undefined }}>
      <div className="sidebar-header">
        <div className="sidebar-title">Rhombus Preview</div>
        <div className="sidebar-subtitle">Context files</div>
        <label style={{ marginTop: '8px' }}>
          <input
            type="password"
            className="endpoint-input"
            value={endpoint}
            onChange={(e) => onChangeEndpoint(e.target.value)}
            onFocus={(e) => e.target.type = 'text'}
            onBlur={(e) => e.target.type = 'password'}
            title="Backend Endpoint URL"
          />
        </label>
      </div>
      <div className="sidebar-content">
        {tree.length === 0 ?
          <div className="sidebar-empty">No files loaded.</div>
        :
          <div className="filetree">{tree.map((node) => <TreeNode key={node.key} node={node} selectedKey={selectedKey} onSelectFile={onSelectFile} depth={0} />)}</div>}
      </div>
    </aside>
  )
}
