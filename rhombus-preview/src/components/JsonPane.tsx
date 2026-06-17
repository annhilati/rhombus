import { useRef, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import type { ContextFile } from '../types'
import { prettyRegistryTitle } from '../lib/registry'

interface JsonPaneProps {
  file: ContextFile
  allFiles: ContextFile[]
  onSelectFile: (file: ContextFile) => void
  width?: number
}

function findStringAtCol(line: string, col: number): string | null {
  const regex = /"([^"\\]*(?:\\.[^"\\]*)*)"/g
  let match
  while ((match = regex.exec(line)) !== null) {
    const startCol = match.index + 2
    const endCol = startCol + match[1].length - 1
    if (col >= startCol && col <= endCol) {
      return match[1]
    }
  }
  return null
}

export default function JsonPane({ file, allFiles, onSelectFile, width }: JsonPaneProps) {
  const value = JSON.stringify(file.content ?? null, null, 2) ?? 'null'

  const allFilesRef = useRef(allFiles)
  const onSelectFileRef = useRef(onSelectFile)

  useEffect(() => {
    allFilesRef.current = allFiles
    onSelectFileRef.current = onSelectFile
  }, [allFiles, onSelectFile])

  const handleEditorMount = (editor: any, monaco: any) => {
    const provider = monaco.languages.registerLinkProvider('json', {
      provideLinks: (model: any) => {
        const links: any[] = []
        const lines = model.getLinesContent()
        lines.forEach((line: string, i: number) => {
          const regex = /"([^"\\]*(?:\\.[^"\\]*)*)"/g
          let match
          while ((match = regex.exec(line)) !== null) {
            const str = match[1]
            const target = allFilesRef.current.find((f) => f.id === str || f.id === str + '.json')
            if (target) {
              links.push({
                range: new monaco.Range(i + 1, match.index + 2, i + 1, match.index + 2 + str.length),
                url: `rhombus://file/${target.id}`,
                tooltip: `Go to ${target.id}`
              })
            }
          }
        })
        return { links }
      }
    })

    editor.onMouseDown((e: any) => {
      if (e.target.type === monaco.editor.MouseTargetType.CONTENT_TEXT) {
        if (e.event.ctrlKey || e.event.metaKey) {
          const model = editor.getModel()
          const lineContent = model.getLineContent(e.target.position.lineNumber)
          const match = findStringAtCol(lineContent, e.target.position.column)
          if (match) {
            const target = allFilesRef.current.find((f) => f.id === match || f.id === match + '.json')
            if (target) {
              e.event.preventDefault()
              e.event.stopPropagation()
              onSelectFileRef.current(target)
            }
          }
        }
      }
    })

    editor.onDidDispose(() => {
      provider.dispose()
    })
  }

  return (
    <section className="pane pane-json" style={{ width: width ? `${width}px` : undefined, flex: width ? 'none' : undefined }}>
      <div className="pane-header">
        <div className="pane-title">{prettyRegistryTitle(file.registry)}</div>
        <div className="pane-meta">{file.id}</div>
      </div>
      <div className="pane-body">
        <Editor
          language="json"
          value={value}
          onMount={handleEditorMount}
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
