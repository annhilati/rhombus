import { useEffect, useMemo, useState, useRef, useCallback } from 'react'

import Sidebar from './components/Sidebar'
import Resizer from './components/Resizer'
import Workspace, { WorkspaceRef } from './components/Workspace'

import { getEventsEndpoint, fetchFilesFromService } from './lib/api'
import { fileKey } from './lib/registry'
import { buildTree } from './lib/tree'
import { useLocalStorage } from './lib/storage'
import { fetchVanillaData } from './lib/deepslate'
import type { RhombusContextFile } from './types'

/**
 * The main application component that manages state for loaded files, selected files,
 * UI layout configurations (like resizer widths), and handles live-reloading via SSE.
 */
export default function App() {
    const [endpoint, setEndpoint]               = useLocalStorage<string>('rhombus.endpoint', 'http://127.0.0.1:8000')
    const [selectedFileKey, setSelectedFileKey] = useLocalStorage<string | null>('rhombus.selectedKey', null)
    const [files, setFiles]                     = useState<RhombusContextFile[]>([])
    const [status, setStatus]                   = useState<'loading' | 'ready' | 'error'>('loading')
    const [error, setError]                     = useState<string | null>(null)

    const [sidebarWidth, setSidebarWidth] = useLocalStorage('rhombus.sidebarWidth', 320)
    const [toastMessage, setToastMessage] = useState<string | null>(null)
    const toastTimeout = useRef<number | null>(null)
    const workspaceRef = useRef<WorkspaceRef>(null)

    /** Displays a toast for a duration of given milliseconds. */
    const showToast = useCallback((message: string, duration = 3000) => {
        setToastMessage(message)

        if (toastTimeout.current) {
            window.clearTimeout(toastTimeout.current)
        }

        toastTimeout.current = window.setTimeout(() => {
            setToastMessage(null)
            toastTimeout.current = null
        }, duration)
    }, [])

    useEffect(() => {
        let cancelled = false

        /** Loads the files from endpoint and vanilla resources */
        async function initializeData() {

            try {
                // Files
                const [loadedFiles] = await Promise.all([
                    fetchFilesFromService(endpoint),
                    fetchVanillaData().catch(e => {
                        console.warn('Failed to fetch vanilla data', e)
                        showToast('Failed fetching vanilla resources from Misode.')
                    })
                ])
                
                // Scripts
                try {
                    const response = await fetch(`${endpoint}/addons/scripts`)
                    if (response.ok) {
                        const scripts = await response.json()
                        const { transform } = await import('sucrase')
                        for (const script of scripts) {
                            try {
                                if (script.name.endsWith('.ts')) {
                                    const tsCode = await fetch(`${endpoint}${script.url}?t=${Date.now()}`).then(r => r.text())
                                    const jsCode = transform(tsCode, { transforms: ['typescript'] }).code
                                    const blob = new Blob([jsCode], { type: 'application/javascript' })
                                    const url = URL.createObjectURL(blob)
                                    await import(/* @vite-ignore */ url)
                                } else {
                                    await import(/* @vite-ignore */ `${endpoint}${script.url}?t=${Date.now()}`)
                                }
                            } catch (e) {
                                console.error(`Failed to load addon script: ${script.url}`, e)
                            }
                        }
                    }
                } catch (e) {
                    console.warn('Failed to fetch addons from service', e)
                }

                if (cancelled) return
                
                setFiles(loadedFiles)
                showToast('✨ Files were changed')
                
                setSelectedFileKey((current) => current ?? null)
                setStatus('ready')
                setError(null)
            } catch (err) {
                if (cancelled) return
                setStatus('error')
                setError(err instanceof Error ? err.message : 'Unknown error')
            }
        }

        // Initial load
        initializeData()

        // Setup SSE for live updates
        let eventSource: EventSource | null = null
        try {
            const eventsUrl = getEventsEndpoint(endpoint)
            eventSource = new EventSource(eventsUrl)
            
            eventSource.onmessage = (event) => {
                if (event.data === 'update') {
                    initializeData()
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

    const selectedFile = useMemo(() => files.find((file) => fileKey(file) === selectedFileKey) ?? files[0] ?? null, [files, selectedFileKey])

    return (
        <div className="app">
            <Sidebar 
                tree={fileTree} 
                selectedKey={selectedFileKey} 
                onSelectFile={(file, newTab = false) => {
                    setSelectedFileKey(fileKey(file))
                    workspaceRef.current?.openFile(file, newTab)
                }} 
                endpoint={endpoint}
                onChangeEndpoint={setEndpoint}
                width={sidebarWidth} 
            />
            <Resizer value={sidebarWidth} onChange={setSidebarWidth} min={200} max={850} />
            <main className="main-area">
                {status === 'loading' && <div className="status-banner">Loading files from {endpoint}...</div>}
                {status === 'error'   && <div className="status-banner status-error">Could not load files: {error}</div>}
                
                {status === 'ready' && (
                    <Workspace ref={workspaceRef} files={files} selectedFile={selectedFile} onSelectFile={(f) => {
                        setSelectedFileKey(fileKey(f))
                        workspaceRef.current?.openFile(f, false)
                    }} />
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
