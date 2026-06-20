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

function renderSplineSVG(spline: any): string | null {
  if (!spline?.points || !Array.isArray(spline.points)) return null;
  const validPoints: {x: number, y: number, d: number}[] = [];
  
  for (const p of spline.points) {
    if (typeof p.location === 'number' && typeof p.value === 'number') {
      validPoints.push({ x: p.location, y: p.value, d: typeof p.derivative === 'number' ? p.derivative : 0 });
    }
  }
  
  if (validPoints.length < 2) return null;
  validPoints.sort((a, b) => a.x - b.x);
  
  let minX = validPoints[0].x, maxX = validPoints[validPoints.length - 1].x;
  let minY = Math.min(...validPoints.map(p => p.y));
  let maxY = Math.max(...validPoints.map(p => p.y));
  
  if (minX === maxX) { minX -= 1; maxX += 1; }
  if (minY === maxY) { minY -= 1; maxY += 1; }
  
  const yPad = (maxY - minY) * 0.15;
  minY -= yPad; maxY += yPad;
  
  const width = 340, height = 160, padX = 40, padY = 20;
  const mapX = (x: number) => padX + ((x - minX) / (maxX - minX)) * (width - padX * 2);
  const mapY = (y: number) => height - padY - ((y - minY) / (maxY - minY)) * (height - padY * 2);
  
  let path = `M ${mapX(validPoints[0].x)} ${mapY(validPoints[0].y)}`;
  for (let i = 0; i < validPoints.length - 1; i++) {
    const p0 = validPoints[i], p1 = validPoints[i+1];
    const dx = p1.x - p0.x;
    const c0x = p0.x + dx / 3, c0y = p0.y + (dx / 3) * p0.d;
    const c1x = p1.x - dx / 3, c1y = p1.y - (dx / 3) * p1.d;
    path += ` C ${mapX(c0x)} ${mapY(c0y)}, ${mapX(c1x)} ${mapY(c1y)}, ${mapX(p1.x)} ${mapY(p1.y)}`;
  }
  
  const zeroY = minY <= 0 && maxY >= 0 ? mapY(0) : height - padY;
  const zeroX = minX <= 0 && maxX >= 0 ? mapX(0) : padX;
  
  const svg = `
<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg" style="background:#1e1e1e; border-radius:6px; border: 1px solid #333;">
  <line x1="${padX}" y1="${zeroY}" x2="${width-padX}" y2="${zeroY}" stroke="#555" stroke-width="1" />
  <line x1="${zeroX}" y1="${padY}" x2="${zeroX}" y2="${height-padY}" stroke="#555" stroke-width="1" />
  <path d="${path}" fill="none" stroke="#35aaf3" stroke-width="2" />
  ${validPoints.map(p => `<circle cx="${mapX(p.x)}" cy="${mapY(p.y)}" r="3" fill="#fff" />`).join('')}
  <text x="${padX}" y="${height-5}" fill="#aaa" font-size="10" font-family="sans-serif">${minX.toFixed(2)}</text>
  <text x="${width-padX}" y="${height-5}" fill="#aaa" font-size="10" font-family="sans-serif" text-anchor="end">${maxX.toFixed(2)}</text>
  <text x="${padX-6}" y="${mapY(maxY)}" fill="#aaa" font-size="10" font-family="sans-serif" text-anchor="end" dominant-baseline="middle">${maxY.toFixed(2)}</text>
  <text x="${padX-6}" y="${mapY(minY)}" fill="#aaa" font-size="10" font-family="sans-serif" text-anchor="end" dominant-baseline="middle">${minY.toFixed(2)}</text>
</svg>
`;
  return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg.trim())))}`;
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

    const providers: any[] = [];
    
    providers.push(
      monaco.languages.registerCodeLensProvider('json', {
        provideCodeLenses: (model: any) => {
          const lenses: any[] = [];
          const lines = model.getLinesContent();
          for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes('"minecraft:spline"')) {
              lenses.push({
                range: new monaco.Range(i + 1, 1, i + 1, 1),
                id: `spline-lens-${i}`,
                command: { id: "", title: "Hover below to preview spline" }
              });
            }
          }
          return { lenses, dispose: () => {} };
        },
        resolveCodeLens: (model: any, codeLens: any) => codeLens
      })
    );

    providers.push(
      monaco.languages.registerHoverProvider('json', {
        provideHover: (model: any, position: any) => {
          const lineContent = model.getLineContent(position.lineNumber);
          if (lineContent.includes('"minecraft:spline"')) {
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
                  
                  // Minecraft stores the spline either directly or wrapped inside 'spline' key for density functions
                  const splineData = Array.isArray(obj?.points) ? obj : (Array.isArray(obj?.spline?.points) ? obj.spline : null);

                  if (splineData) {
                    const svgUri = renderSplineSVG(splineData);
                    if (svgUri) {
                      return {
                        range: new monaco.Range(position.lineNumber, 1, position.lineNumber, lineContent.length),
                        contents: [
                          { value: `**Spline Preview**` },
                          { value: `![Spline](${svgUri})` }
                        ]
                      };
                    } else {
                      return {
                        range: new monaco.Range(position.lineNumber, 1, position.lineNumber, lineContent.length),
                        contents: [{ value: `*Spline data found, but preview could not be generated (possibly due to too few numerical points).*` }]
                      };
                    }
                  } else {
                    return {
                      range: new monaco.Range(position.lineNumber, 1, position.lineNumber, lineContent.length),
                      contents: [{ value: `*No spline points found*` }]
                    };
                  }
                } catch (e) {
                   return {
                      range: new monaco.Range(position.lineNumber, 1, position.lineNumber, lineContent.length),
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

    editor.onDidDispose(() => {
      providers.forEach((p) => p.dispose());
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
