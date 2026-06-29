import { useEffect, useRef, useState, useMemo } from 'react'
import type { ReactNode } from 'react'
import type { RhombusContextFile } from '../types'
import { loadDeepslateRuntime } from '../lib/deepslate'

export interface ViewState {
    zoom: number
    panX: number
    panY: number
    panZ: number
    yLevel: number
    zLevel: number
    viewMode: 'top' | 'side'
    seed: bigint
    pixelSize: number
}

export interface CanvasVisualizerProps {
    file: RhombusContextFile
    contextFiles: RhombusContextFile[]
    parseError?: string | null
    onDraw: (
        image: ImageData,
        viewState: ViewState,
        onError: (msg: string | null) => void
    ) => void
    renderTooltip: (
        viewState: ViewState,
        worldX: number,
        worldY: number,
        worldZ: number
    ) => ReactNode
}

export default function CanvasVisualizer({ file, contextFiles, parseError, onDraw, renderTooltip }: CanvasVisualizerProps) {
    const wrapperRef = useRef<HTMLDivElement | null>(null)
    const canvasRef = useRef<HTMLCanvasElement | null>(null)
    const [zoom, setZoom] = useState(1)
    const [panX, setPanX] = useState(0)
    const [panY, setPanY] = useState(64)
    const [panZ, setPanZ] = useState(0)
    const [yLevel, setYLevel] = useState(64)
    const [zLevel, setZLevel] = useState(0)
    const [viewMode, setViewMode] = useState<'top' | 'side'>('top')
    const [runtimeReady, setRuntimeReady] = useState(false)
    const [deepslateErrors, setDeepslateErrors] = useState<{fileId: string, error: string}[]>([])
    const dragRef = useRef<{ active: boolean; x: number; y: number } | null>(null)
    const [hoverCoords, setHoverCoords] = useState<{ x: number, y: number, z: number, worldX: number, worldY: number, worldZ: number } | null>(null)
    const [renderTimeMs, setRenderTimeMs] = useState<number | null>(null)
    const [runtimeError, setRuntimeError] = useState<string | null>(null)
    const [seedStr, setSeedStr] = useState('0')

    const seed = useMemo(() => {
        if (/^-?\d+$/.test(seedStr)) {
            try { return BigInt(seedStr) } catch {}
        }
        let hash = 0
        for (let i = 0; i < seedStr.length; i++) {
            hash = (Math.imul(31, hash) + seedStr.charCodeAt(i)) | 0
        }
        return BigInt(hash)
    }, [seedStr])

    const scale = useMemo(() => {
        const targetBlocks = 100 / zoom
        const magnitude = Math.pow(10, Math.floor(Math.log10(targetBlocks)))
        const normalized = targetBlocks / Math.max(1, magnitude)
        
        let niceBlocks: number
        if (normalized < 1.5) niceBlocks = 1 * magnitude
        else if (normalized < 3.5) niceBlocks = 2 * magnitude
        else if (normalized < 7.5) niceBlocks = 5 * magnitude
        else niceBlocks = 10 * magnitude
        
        niceBlocks = Number(niceBlocks.toPrecision(2))
        
        return {
            blocks: niceBlocks,
            pixels: niceBlocks * zoom
        }
    }, [zoom])

    const fileDependencies = useMemo(() => {
        const deps = new Set<string>()
        const filesMap = new Map<string, any>()
        for (const f of contextFiles) filesMap.set(f.id, f.content)

        function crawl(id: string) {
            if (deps.has(id)) return
            deps.add(id)
            const content = filesMap.get(id)
            if (!content) return
            
            const str = JSON.stringify(content)
            const matches = str.matchAll(/"([a-z0-9_-]+:[a-z0-9_/-]+)"/g)
            for (const match of matches) {
                if (filesMap.has(match[1])) {
                    crawl(match[1])
                }
            }
        }
        crawl(file.id)
        return deps
    }, [file.id, contextFiles])

    useEffect(() => {
        let cancelled = false
        const runtime = loadDeepslateRuntime()
        runtime.registerFiles(contextFiles)
        if (!cancelled) {
            setDeepslateErrors(runtime.parseErrors)
            setRuntimeReady(true)
        }
        return () => { cancelled = true }
    }, [contextFiles])

    const localErrors = useMemo(() => deepslateErrors.filter(e => fileDependencies.has(e.fileId)), [deepslateErrors, fileDependencies])

    const viewState: ViewState = useMemo(() => ({
        zoom, panX, panY, panZ, yLevel, zLevel, viewMode, seed, pixelSize: 2
    }), [zoom, panX, panY, panZ, yLevel, zLevel, viewMode, seed])

    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas || !runtimeReady) return
        if (parseError || localErrors.length > 0) {
            setRuntimeError(null)
            return
        }

        const update = () => {
            const ctx2d = canvas.getContext('2d', { willReadFrequently: true })
            if (!ctx2d) return
            
            const pixelSize = viewState.pixelSize
            const rect = canvas.getBoundingClientRect()
            const width = Math.max(1, Math.floor(rect.width / pixelSize))
            const height = Math.max(1, Math.floor(rect.height / pixelSize))
            
            if (canvas.width !== width) canvas.width = width
            if (canvas.height !== height) canvas.height = height

            // clear errors on new draw
            setRuntimeError(null)

            const image = ctx2d.createImageData(width, height)
            
            const t0 = performance.now()
            onDraw(image, viewState, setRuntimeError)
            ctx2d.putImageData(image, 0, 0)
            const t1 = performance.now()
            setRenderTimeMs(t1 - t0)
        }
        update()

        const observer = new ResizeObserver(update)
        if (wrapperRef.current) observer.observe(wrapperRef.current)
        return () => observer.disconnect()
    }, [viewState, runtimeReady, parseError, localErrors, onDraw])

    return (
        <section className="pane pane-visualizer">
            <div
                ref={wrapperRef}
                className="pane-body visualizer-canvas-wrap"
                onPointerLeave={() => setHoverCoords(null)}
                onPointerDown={(event) => {
                    dragRef.current = { active: true, x: event.clientX, y: event.clientY }
                    ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
                }}
                onPointerMove={(event) => {
                    const drag = dragRef.current
                    if (drag?.active) {
                        const dx = event.clientX - drag.x
                        const dy = event.clientY - drag.y
                        dragRef.current = { active: true, x: event.clientX, y: event.clientY }
                        setPanX((value) => value - dx / zoom)
                        if (viewMode === 'top') {
                            setPanZ((value) => value - dy / zoom)
                        } else {
                            setPanY((value) => value + dy / zoom)
                        }
                    }
                    
                    const rect = event.currentTarget.getBoundingClientRect()
                    const px = event.clientX - rect.left
                    const py = event.clientY - rect.top
                    const worldX = panX + (px - rect.width / 2) / zoom
                    
                    if (viewMode === 'top') {
                        const worldZ = panZ + (py - rect.height / 2) / zoom
                        setHoverCoords({ 
                            x: Math.floor(worldX), y: Math.floor(yLevel), z: Math.floor(worldZ),
                            worldX, worldY: yLevel, worldZ 
                        })
                    } else {
                        const worldY = panY - (py - rect.height / 2) / zoom
                        setHoverCoords({ 
                            x: Math.floor(worldX), y: Math.floor(worldY), z: Math.floor(zLevel),
                            worldX, worldY, worldZ: zLevel
                        })
                    }
                }}
                onPointerUp={(event) => {
                    dragRef.current = null
                    ;(event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId)
                }}
                onWheel={(event) => {
                    event.preventDefault()
                    const factor = event.deltaY > 0 ? 0.92 : 1.08
                    setZoom((value) => {
                        const next = Math.min(20, Math.max(0.1, value * factor))
                        return Math.round(next * 100) / 100
                    })
                }}
            >
                <div className="visualizer-settings-panel" onPointerDown={(e) => e.stopPropagation()} onPointerMove={(e) => e.stopPropagation()} onPointerUp={(e) => e.stopPropagation()} onWheel={(e) => e.stopPropagation()}>
                    <div className="visualizer-toolbar">
                        <label>
                            <button type="button" onClick={() => setViewMode(v => v === 'top' ? 'side' : 'top')} style={{ width: '90px' }}>
                                {viewMode === 'top' ? 'Top View' : 'Side View'}
                            </button>
                        </label>
                        <label>Zoom: {Math.round(zoom * 100) / 100}x
                            <input type="range" min="0.1" max="5" step="0.1" value={zoom} onChange={(event) => setZoom(Number(event.target.value))} />
                        </label>
                        {viewMode === 'top' ? (
                            <label>Y: {yLevel}
                                <input type="range" min="-64" max="320" step="1" value={yLevel} onChange={(event) => setYLevel(Number(event.target.value))} />
                            </label>
                        ) : (
                            <label>Z: {zLevel}
                                <input type="range" min="-200" max="200" step="1" value={zLevel} onChange={(event) => setZLevel(Number(event.target.value))} />
                            </label>
                        )}
                        <label>Seed
                            <div style={{ display: 'flex', gap: '4px' }}>
                                <input type="text" value={seedStr} onChange={(event) => setSeedStr(event.target.value)} style={{ width: '85px' }} />
                                <button type="button" onClick={() => setSeedStr(Math.floor(Math.random() * 2147483647).toString())} title="Randomize Seed">🎲</button>
                            </div>
                        </label>
                        <label>
                            <button type="button" onClick={() => { setZoom(2); setPanX(0); setPanY(64); setPanZ(0); setYLevel(64); setZLevel(0); setSeedStr('0'); setViewMode('top') }}>Reset</button>
                        </label>
                    </div>
                    <div className="visualizer-settings-handle">
                        <span>Hover to open settings</span>
                    </div>
                </div>
                {hoverCoords && (
                    <div className="visualizer-tooltip">
                        {runtimeReady ? `Deepslate ready:${renderTimeMs !== null ? ` ${Math.round(renderTimeMs)}ms` : ''}` : 'Deepslate loading'}
                        <br/> 
                        {renderTooltip(viewState, hoverCoords.worldX, hoverCoords.worldY, hoverCoords.worldZ)}
                    </div>
                )}
                <div className="scale">
                    <div className="scale-shape" style={{ width: scale.pixels }} />
                    <div className="scale-text">{scale.blocks} blocks</div>
                </div>
                <canvas ref={canvasRef} className="visualizer-canvas" />
                {(parseError || runtimeError) && (
                    <div className="error-banner">
                        <strong>Deepslate Error:</strong> {parseError || runtimeError}
                    </div>
                )}
                {localErrors.length > 0 && (
                    <div className="error-banner" style={{ marginTop: '10px' }}>
                        <strong>Cannot visualize due to {localErrors.length} error{localErrors.length > 1 ? 's' : ''}</strong>
                        <ul style={{ margin: '5px 0 0 20px', padding: 0 }}>
                            {localErrors.map((err, i) => (
                                <li key={i}><strong>[{err.fileId}]</strong> {err.error}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </section>
    )
}
