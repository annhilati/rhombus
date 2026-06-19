import { useRef, useEffect, useState } from 'react'
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

  const editorRef = useRef<any>(null)
  const monacoRef = useRef<any>(null)
  const decorationsCollectionRef = useRef<any>(null)

  const updateDecorations = () => {
    if (!editorRef.current || !monacoRef.current) return
    const editor = editorRef.current
    const monaco = monacoRef.current
    const model = editor.getModel()
    if (!model) return

    const links: any[] = []
    const lines = model.getLinesContent()
    lines.forEach((line: string, i: number) => {
      const regex = /"([^"\\]*(?:\\.[^"\\]*)*)"/g
      let match
      while ((match = regex.exec(line)) !== null) {
        const str = match[1]
        const target = allFiles.find((f) => f.id === str || f.id === str + '.json')
        if (target) {
          links.push({
            range: new monaco.Range(i + 1, match.index + 2, i + 1, match.index + 2 + str.length),
            options: {
              inlineClassName: 'monaco-custom-link',
              hoverMessage: { value: `Ctrl+Click to open **${target.id}**` }
            }
          })
        }
      }
    })

    if (decorationsCollectionRef.current) {
      decorationsCollectionRef.current.set(links)
    }
  }

  useEffect(() => {
    allFilesRef.current = allFiles
    onSelectFileRef.current = onSelectFile
    updateDecorations()
  }, [allFiles, onSelectFile, value])

  const handleEditorMount = (editor: any, monaco: any) => {
    editorRef.current = editor
    monacoRef.current = monaco
    decorationsCollectionRef.current = editor.createDecorationsCollection()
    
    updateDecorations()

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
      editorRef.current = null
      monacoRef.current = null
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
            fontSize: 16,
            scrollBeyondLastLine: false,
            wordWrap: 'off',
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
