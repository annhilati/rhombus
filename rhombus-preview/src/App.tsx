import { useEffect, useMemo, useState } from 'react'

import Sidebar from './components/Sidebar'
import JsonPane from './components/JsonPane'
import VisualizerPane from './components/VisualizerPane'
import Resizer from './components/Resizer'

import { getContextEndpoint, loadContextFiles } from './lib/api'
import { fileKey, normalizeRegistryName } from './lib/registry'
import { buildTree } from './lib/tree'
import { useLocalStorage } from './lib/storage'
import type { ContextFile } from './types'

export default function App() {
  const [files, setFiles]             = useState<ContextFile[]>([])
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [status, setStatus]           = useState<'loading' | 'ready' | 'error'>('loading')
  const [error, setError]             = useState<string | null>(null)

  const [sidebarWidth, setSidebarWidth]   = useLocalStorage('rhombus.sidebarWidth', 320)
  const [jsonPaneWidth, setJsonPaneWidth] = useLocalStorage('rhombus.jsonPaneWidth', 400)

  useEffect(() => {
    let cancelled = false

    async function run() {
      try {
        const loadedFiles = await loadContextFiles(getContextEndpoint())
        if (cancelled) return
        setFiles(loadedFiles)
        setSelectedKey((current) => current ?? (loadedFiles[0] ? fileKey(loadedFiles[0]) : null))
        setStatus('ready')
        setError(null)
      } catch (cause) {
        if (cancelled) return
        setStatus('error')
        setError(cause instanceof Error ? cause.message : 'Unknown error')
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [])

  const fileTree = useMemo(() => buildTree(files), [files])

  const selectedFile = useMemo(() => files.find((file) => fileKey(file) === selectedKey) ?? files[0] ?? null, [files, selectedKey])
  const registryLabel = selectedFile ? normalizeRegistryName(selectedFile.registry) : null


  return (
    <div className="app">
      <Sidebar tree={fileTree} selectedKey={selectedKey} onSelectFile={(file) => setSelectedKey(fileKey(file))} width={sidebarWidth} />
      <Resizer onResize={(dx) => setSidebarWidth((w) => Math.max(200, Math.min(800, w + dx)))} />
      <main className="main-area">
        {status === 'loading' &&                  <div className="status-banner">Loading context files from {getContextEndpoint()}...</div>}
        {status === 'error'   &&                  <div className="status-banner status-error">Could not load files: {error}</div>}
        {status === 'ready'   && !selectedFile && <div className="status-banner">No file selected.</div>}
        
        {selectedFile && (
          <div className={`workspace ${registryLabel ? 'has-visualizer' : 'json-only'}`}>
            <JsonPane file={selectedFile} allFiles={files} onSelectFile={(f) => setSelectedKey(fileKey(f))} width={registryLabel ? jsonPaneWidth : undefined} />
            {registryLabel && <Resizer onResize={(dx) => setJsonPaneWidth((w) => Math.max(200, Math.min(1200, w + dx)))} />}
            <VisualizerPane file={selectedFile} allFiles={files} />
          </div>
        )}
      </main>
    </div>
  )
}
