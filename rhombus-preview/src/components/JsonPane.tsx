import Editor from '@monaco-editor/react'
import type { ContextFile } from '../types'
import { prettyRegistryTitle } from '../lib/registry'

interface JsonPaneProps {
  file: ContextFile
}

export default function JsonPane({ file }: JsonPaneProps) {
  const value = JSON.stringify(file.content ?? null, null, 2) ?? 'null'

  return (
    <section className="pane pane-json">
      <div className="pane-header">
        <div className="pane-title">{prettyRegistryTitle(file.registry)}</div>
        <div className="pane-meta">{file.id}</div>
      </div>
      <div className="pane-body">
        <Editor
          language="json"
          value={value}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 13,
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            automaticLayout: true,
            renderLineHighlight: 'none',
            tabSize: 2,
          }}
          theme="vs-dark"
          loading={<div className="pane-loading">Loading editor…</div>}
        />
      </div>
    </section>
  )
}
