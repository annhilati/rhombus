import { useRef, useEffect } from 'react'

import Editor, { Monaco, OnMount } from '@monaco-editor/react'
import type { editor, languages, Position } from 'monaco-editor'

import type { RhombusContextFile } from '../types'
import { prettyRegistryTitle } from '../lib/registry'
import { renderSplineSVG } from '../lib/splinePreview'

interface FileviewPaneProps {
  file: RhombusContextFile
  contextFiles: RhombusContextFile[]
  onSelectFile: (file: RhombusContextFile) => void
  width?: number
}

/**
 * Finds and extracts a string literal within a line of JSON based on the given column index.
 * Useful for resolving clicked file references in the editor.
 */
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


/**
 * Renders a Monaco Editor pane displaying the JSON content of the selected file.
 * Automatically adds interactive links to other files and hover previews for spline data.
 */
export default function FileviewPane({ file, contextFiles, onSelectFile, width }: FileviewPaneProps) {
  const value = typeof file.content === 'string' ? file.content : (JSON.stringify(file.content ?? null, null, 2) ?? 'null')

  const allFilesRef = useRef(contextFiles)
  const onSelectFileRef = useRef(onSelectFile)

  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null)
  const monacoRef = useRef<Monaco | null>(null)
  const decorationsCollectionRef = useRef<editor.IEditorDecorationsCollection | null>(null)

  const updateDecorations = () => {
    if (!editorRef.current || !monacoRef.current) return
    const editorInstance = editorRef.current
    const monacoInstance = monacoRef.current
    const model = editorInstance.getModel()
    if (!model) return

    const links: editor.IModelDeltaDecoration[] = []
    const lines = model.getLinesContent()
    lines.forEach((line: string, i: number) => {
      const regex = /"([^"\\]*(?:\\.[^"\\]*)*)"/g
      let match
      while ((match = regex.exec(line)) !== null) {
        const str = match[1]
        const target = contextFiles.find((f) => f.id === str || f.id === str + '.json')
        if (target) {
          links.push({
            range: new monacoInstance.Range(i + 1, match.index + 2, i + 1, match.index + 2 + str.length),
            options: {
              inlineClassName: 'monaco-custom-link',
              hoverMessage: { value: `View definition of **${target.id}** (Ctrl + Click)` }
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
    allFilesRef.current = contextFiles
    onSelectFileRef.current = onSelectFile
    updateDecorations()
  }, [contextFiles, onSelectFile, value])

  const handleEditorMount: OnMount = (editorInstance, monacoInstance) => {
    editorRef.current = editorInstance
    monacoRef.current = monacoInstance
    decorationsCollectionRef.current = editorInstance.createDecorationsCollection()
    
    updateDecorations()

    editorInstance.onMouseDown((e: editor.IEditorMouseEvent) => {
      if (e.target.type === monacoInstance.editor.MouseTargetType.CONTENT_TEXT && e.target.position) {
        if (e.event.ctrlKey || e.event.metaKey) {
          const model = editorInstance.getModel()
          if (!model) return;
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

    const providers: { dispose: () => void }[] = [];
    
    // Spline Preview CodeLens Information
    providers.push(
      monacoInstance.languages.registerCodeLensProvider('json', {
        provideCodeLenses: (model: editor.ITextModel) => {
          const lenses: languages.CodeLens[] = [];
          const lines = model.getLinesContent();
          const regex = /"type"\s*:\s*"(minecraft:)?spline"/;
          for (let i = 0; i < lines.length; i++) {
            if (regex.test(lines[i])) {
              lenses.push({
                range: new monacoInstance.Range(i + 1, 1, i + 1, 1),
                id: `spline-lens-${i}`,
                command: { id: "", title: "Hover below to preview spline function" }
              });
            }
          }
          return { lenses, dispose: () => {} };
        },
        resolveCodeLens: (model: editor.ITextModel, codeLens: languages.CodeLens) => codeLens
      })
    );

    // Spline Preview Hover
    providers.push(
      monacoInstance.languages.registerHoverProvider('json', {
        provideHover: (model: editor.ITextModel, position: Position) => {
          const lineContent = model.getLineContent(position.lineNumber);
          const regex = /"type"\s*:\s*"(minecraft:)?spline"/;
          if (regex.test(lineContent)) {
            const text = model.getValue();
            const offset = model.getOffsetAt({ lineNumber: position.lineNumber, column: 1 });
            let open = 0, start = -1, end = -1;
            for(let i = offset; i >= 0; i--) {
              if (text[i] === '}') open--;
              if (text[i] === '{') {
                open++;
                if (open > 0) { start = i; break; }
              }
            }
            if (start !== -1) {
              open = 0;
              for(let i = start; i < text.length; i++) {
                if (text[i] === '{') open++;
                if (text[i] === '}') {
                  open--;
                  if (open === 0) { end = i; break; }
                }
              }
              if (end !== -1) {
                try {
                  const obj = JSON.parse(text.substring(start, end + 1));
                  const splineData = Array.isArray(obj?.points) ? obj : (Array.isArray(obj?.spline?.points) ? obj.spline : null);

                  if (splineData) {
                    const result = renderSplineSVG(splineData);
                    if (result?.type === 'success') {
                      return {
                        range: new monacoInstance.Range(position.lineNumber, 1, position.lineNumber, lineContent.length),
                        contents: [
                          { value: `**Spline Preview**` },
                          { value: `![Spline](${result.svg})` }
                        ]
                      };
                    } else if (result?.type === 'error') {
                      return {
                        range: new monacoInstance.Range(position.lineNumber, 1, position.lineNumber, lineContent.length),
                        contents: [{ value: result.message }]
                      };
                    } else {
                      return {
                        range: new monacoInstance.Range(position.lineNumber, 1, position.lineNumber, lineContent.length),
                        contents: [{ value: `*Cannot preview spline. Too few spline points*` }]
                      };
                    }
                  } else {
                    return {
                      range: new monacoInstance.Range(position.lineNumber, 1, position.lineNumber, lineContent.length),
                      contents: [{ value: `*Missing spline points*` }]
                    };
                  }
                } catch (e) {
                   return {
                      range: new monacoInstance.Range(position.lineNumber, 1, position.lineNumber, lineContent.length),
                      contents: [{ value: `*Failed parsing JSON*` }]
                   };
                }
              }
            }
          }
          return null;
        }
      })
    );

    editorInstance.onDidDispose(() => {
      providers.forEach((p) => p.dispose());
      editorRef.current = null
      monacoRef.current = null
    })
  }

  return (
    <section className="pane pane-json" style={{ width: width ? `${width}px` : undefined, flex: width ? 'none' : undefined }}>
      {/* <div className="pane-header">
        <div className="pane-title">{prettyRegistryTitle(file.registry)}</div>
        <div className="pane-meta">{file.id} ({file.language})</div>
      </div> */}
      <div className="pane-body">
        <Editor
          language={file.language ? file.language : "json"}
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
