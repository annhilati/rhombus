import { useEffect, useMemo, useState } from 'react'
import Sidebar from './components/Sidebar'
import JsonPane from './components/JsonPane'
import VisualizerPane from './components/VisualizerPane'
import { getContextEndpoint, loadContextFiles } from './lib/api'
import { fileKey, normalizeRegistryName } from './lib/registry'
import { buildTree } from './lib/tree'
import type { ContextFile } from './types'

export default function App() {
  const [files, setFiles] = useState<ContextFile[]>([])
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function run() {
      try {
        const loaded = await loadContextFiles(getContextEndpoint())
        if (cancelled) return
        setFiles(loaded)
        setSelectedKey((current) => current ?? (loaded[0] ? fileKey(loaded[0]) : null))
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

  const tree = useMemo(() => buildTree(files), [files])

  const selectedFile = useMemo(() => files.find((file) => fileKey(file) === selectedKey) ?? files[0] ?? null, [files, selectedKey])
  const registryLabel = selectedFile ? normalizeRegistryName(selectedFile.registry) : null

  return (
    <div className="app-shell">
      <Sidebar tree={tree} selectedKey={selectedKey} onSelectFile={(file) => setSelectedKey(fileKey(file))} />
      <main className="main-area">
        {status === 'loading' && <div className="status-banner">Loading context files from {getContextEndpoint()}…</div>}
        {status === 'error' && <div className="status-banner status-error">Could not load files: {error}</div>}
        {status === 'ready' && !selectedFile && <div className="status-banner">No file selected.</div>}
        {selectedFile && (
          <div className={`workspace ${registryLabel ? 'has-visualizer' : 'json-only'}`}>
            <JsonPane file={selectedFile} />
            <VisualizerPane file={selectedFile} allFiles={files} />
          </div>
        )}
      </main>
    </div>
  )
}
