import { useEffect, useMemo, useState, useRef } from 'react'

import Sidebar from './components/Sidebar'
import JsonPane from './components/JsonPane'
import VisualizerPane from './components/VisualizerPane'
import Resizer from './components/Resizer'

import { getEventsEndpoint, loadContextFiles } from './lib/api'
import { fileKey, normalizeRegistryName } from './lib/registry'
import { buildTree } from './lib/tree'
import { useLocalStorage } from './lib/storage'
import { fetchVanillaData } from './lib/deepslate'
import type { ContextFile } from './types'

export default function App() {
  const [endpoint, setEndpoint]       = useLocalStorage<string>('rhombus.endpoint', 'http://127.0.0.1:8000')
  const [files, setFiles]             = useState<ContextFile[]>([])
  const [selectedKey, setSelectedKey] = useLocalStorage<string | null>('rhombus.selectedKey', null)
  const [status, setStatus]           = useState<'loading' | 'ready' | 'error'>('loading')
  const [error, setError]             = useState<string | null>(null)

  const [sidebarWidth, setSidebarWidth]   = useLocalStorage('rhombus.sidebarWidth', 320)
  const [jsonPaneWidth, setJsonPaneWidth] = useLocalStorage('rhombus.jsonPaneWidth', 400)
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const noticeTimeout = useRef<number | null>(null)

  useEffect(() => {
    let cancelled = false

    async function fetchFiles() {
      try {
        const [loadedFiles] = await Promise.all([
          loadContextFiles(endpoint),
          fetchVanillaData().catch(e => {
            console.warn('Failed to fetch vanilla data', e)
            setToastMessage('Fehler beim Laden der Vanilla-Ressourcen (Misode).')
            if (noticeTimeout.current) window.clearTimeout(noticeTimeout.current)
            noticeTimeout.current = window.setTimeout(() => setToastMessage(null), 5000)
          })
        ])
        
        if (cancelled) return
        
        setFiles((prev) => {
          if (prev.length > 0) {
            setToastMessage('✨ Files were changed')
            if (noticeTimeout.current) window.clearTimeout(noticeTimeout.current)
            noticeTimeout.current = window.setTimeout(() => setToastMessage(null), 3000)
          }
          return loadedFiles
        })
        
        setSelectedKey((current) => current ?? (loadedFiles[0] ? fileKey(loadedFiles[0]) : null))
        setStatus('ready')
        setError(null)
      } catch (cause) {
        if (cancelled) return
        setStatus('error')
        setError(cause instanceof Error ? cause.message : 'Unknown error')
      }
    }

    // Initial fetch
    fetchFiles()

    // Setup SSE for live updates
    let eventSource: EventSource | null = null
    try {
      const eventsUrl = getEventsEndpoint(endpoint)
      eventSource = new EventSource(eventsUrl)
      
      eventSource.onmessage = (event) => {
        if (event.data === 'update') {
          fetchFiles()
        }
      }

      eventSource.onerror = () => {
        // Reconnect silently handled by EventSource itself.
      }
    } catch (err) {
      console.warn("Failed to create EventSource:", err)
      setStatus('error')
      setError(err instanceof Error ? err.message : 'Invalid Endpoint URL')
    }

    return () => {
      cancelled = true
      if (eventSource) {
        eventSource.close()
      }
    }
  }, [endpoint])

  const fileTree = useMemo(() => buildTree(files), [files])

  const selectedFile = useMemo(() => files.find((file) => fileKey(file) === selectedKey) ?? files[0] ?? null, [files, selectedKey])
  const registryLabel = selectedFile ? normalizeRegistryName(selectedFile.registry) : null


  return (
    <div className="app">
      <Sidebar 
        tree={fileTree} 
        selectedKey={selectedKey} 
        onSelectFile={(file) => setSelectedKey(fileKey(file))} 
        endpoint={endpoint}
        onChangeEndpoint={setEndpoint}
        width={sidebarWidth} 
      />
      <Resizer value={sidebarWidth} onChange={setSidebarWidth} min={200} max={850} />
      <main className="main-area">
        {status === 'loading' &&                  <div className="status-banner">Loading context files from {endpoint}...</div>}
        {status === 'error'   &&                  <div className="status-banner status-error">Could not load files: {error}</div>}
        {status === 'ready'   && !selectedFile && <div className="status-banner">No file selected.</div>}
        
        {selectedFile && (
          <div className={`workspace ${registryLabel ? 'has-visualizer' : 'json-only'}`}>
            <JsonPane file={selectedFile} allFiles={files} onSelectFile={(f) => setSelectedKey(fileKey(f))} width={registryLabel ? jsonPaneWidth : undefined} />
            {registryLabel && <Resizer value={jsonPaneWidth} onChange={setJsonPaneWidth} min={200} max={1200} />}
            <VisualizerPane file={selectedFile} allFiles={files} />
          </div>
        )}
      </main>

      {toastMessage && (
        <div className="toast-notification">
          {toastMessage}
        </div>
      )}
    </div>
  )
}
