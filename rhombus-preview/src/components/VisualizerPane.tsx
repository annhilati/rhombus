import { useEffect, useRef, useState, useMemo } from 'react'
import type { ContextFile } from '../types'
import { getVisualizationKind, normalizeRegistryName, prettyRegistryTitle } from '../lib/registry'
import { loadDeepslateRuntime } from '../lib/deepslate'
import { DensityFunction, NoiseGeneratorSettings, NoiseParameters, NoiseRouter, NormalNoise, RandomState, XoroshiroRandom, clampedMap } from 'deepslate'
import { viridis } from '../lib/colormap'

interface VisualizerPaneProps {
  file: ContextFile
  allFiles: ContextFile[]
}

function drawCanvas(
  canvas: HTMLCanvasElement,
  sampler: (x: number, y: number, z: number) => number,
  asColor: (n: number) => [number, number, number],
  zoom: number,
  panX: number,
  panY: number,
  panZ: number,
  sliceLevel: number,
  viewMode: 'top' | 'side',
  onError: (msg: string | null) => void
) {
  const pixelSize = 2
  const rect = canvas.getBoundingClientRect()
  const width = Math.max(1, Math.floor(rect.width / pixelSize))
  const height = Math.max(1, Math.floor(rect.height / pixelSize))
  if (canvas.width !== width) canvas.width = width
  if (canvas.height !== height) canvas.height = height

  const ctx2d = canvas.getContext('2d')
  if (!ctx2d) return

  const image = ctx2d.createImageData(width, height)
  onError(null) // clear previous errors

  for (let py = 0; py < height; py += 1) {
    for (let px = 0; px < width; px += 1) {
      const worldX = panX + (px * pixelSize - rect.width / 2) / zoom
      
      try {
        let blockX = Math.floor(worldX)
        let blockY = 0
        let blockZ = 0
        
        if (viewMode === 'top') {
          const worldZ = panZ + (py * pixelSize - rect.height / 2) / zoom
          blockY = sliceLevel
          blockZ = Math.floor(worldZ)
        } else {
          const worldY = panY - (py * pixelSize - rect.height / 2) / zoom
          blockY = Math.floor(worldY)
          blockZ = sliceLevel
        }
        
        const sample = sampler(blockX, blockY, blockZ)
        const color = Number.isNaN(sample) ? [128, 128, 128] : asColor(sample)
        
        const offset = (py * width + px) * 4
        image.data[offset] = color[0]
        image.data[offset + 1] = color[1]
        image.data[offset + 2] = color[2]
        image.data[offset + 3] = 255
      } catch (err) {
        onError(err instanceof Error ? err.message : String(err))
        return // Stop drawing entirely
      }
    }
  }

  ctx2d.putImageData(image, 0, 0)
}

export default function VisualizerPane({ file, allFiles }: VisualizerPaneProps) {
  const kind = getVisualizationKind(file.registry)
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
  const [registryVersion, setRegistryVersion] = useState(0)
  const dragRef = useRef<{ active: boolean; x: number; y: number } | null>(null)
  const [hoverData, setHoverData] = useState<{ x: number, y?: number, z?: number, val: number } | null>(null)
  const [renderTimeMs, setRenderTimeMs] = useState<number | null>(null)
  const [seedStr, setSeedStr] = useState('12345')
  const seed = useMemo(() => {
    try {
      return BigInt(seedStr)
    } catch {
      return 12345n
    }
  }, [seedStr])

  const scale = useMemo(() => {
    const targetBlocks = 100 / zoom
    const magnitude = Math.pow(10, Math.floor(Math.log10(targetBlocks)))
    const normalized = targetBlocks / magnitude
    
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

  useEffect(() => {
    let cancelled = false
    const runtime = loadDeepslateRuntime()
    runtime.registerAllFiles(allFiles)
    if (!cancelled) {
      setRuntimeReady(true)
      setRegistryVersion(v => v + 1)
    }
    return () => {
      cancelled = true
    }
  }, [allFiles])

  const { sampler, asColor, parseError } = useMemo(() => {
    let samplerFn: (x: number, y: number, z: number) => number = () => 0
    let asColorFn: (n: number) => [number, number, number] = () => [0, 0, 0]
    let parseError: string | null = null

    if (!runtimeReady || kind === null) return { sampler: samplerFn, asColor: asColorFn, parseError: null }

    const normalized = normalizeRegistryName(file.registry)
    try {
      if (normalized === 'density_function') {
        const settings = NoiseGeneratorSettings.create({
          noise: { minY: 0, height: 256, xzSize: 1, ySize: 1 },
          noiseRouter: NoiseRouter.create({
            finalDensity: DensityFunction.fromJson(file.content),
          }),
        })
        const state = new RandomState(settings, seed)
        const df = state.router.finalDensity
        samplerFn = (x, y, z) => df.compute({ x, y, z })
        asColorFn = (n) => {
          const clamped = clampedMap(n, -1, 1, 1, 0)
          const col = viridis(clamped <= 0.5 ? clamped - 0.05 : clamped + 0.05)
          return [col[0] * 255, col[1] * 255, col[2] * 255]
        }
      } else if (normalized === 'noise') {
        const random = XoroshiroRandom.create(seed)
        const params = NoiseParameters.fromJson(file.content)
        const noise = new NormalNoise(random, params)
        samplerFn = (x, y, z) => noise.sample(x, y, z)
        asColorFn = (n) => {
          const col = viridis(clampedMap(n, -1, 1, 0, 1))
          return [col[0] * 255, col[1] * 255, col[2] * 255]
        }
      }
    } catch (err) {
      console.error('Error creating deepslate sampler:', err)
      parseError = err instanceof Error ? err.message : String(err)
    }
    return { sampler: samplerFn, asColor: asColorFn, parseError }
  }, [file, runtimeReady, registryVersion, kind, seed])

  const [runtimeError, setRuntimeError] = useState<string | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || kind === null || !runtimeReady) return

    if (parseError) {
      setRuntimeError(null)
      return
    }

    const update = () => {
      const t0 = performance.now()
      drawCanvas(canvas, sampler, asColor, zoom, panX, panY, panZ, viewMode === 'top' ? yLevel : zLevel, viewMode, setRuntimeError)
      const t1 = performance.now()
      setRenderTimeMs(t1 - t0)
    }
    update()

    const observer = new ResizeObserver(update)
    if (wrapperRef.current) observer.observe(wrapperRef.current)

    return () => observer.disconnect()
  }, [sampler, asColor, runtimeReady, zoom, panX, panY, panZ, yLevel, zLevel, viewMode, kind])

  if (kind === null) return null

  return (
    <section className="pane pane-visualizer">
      <div className="pane-header">
        <div className="pane-title">Visualization</div>
        <div className="pane-meta">
          {prettyRegistryTitle(file.registry)} · {runtimeReady ? `deepslate ready${renderTimeMs !== null ? ` (${Math.round(renderTimeMs)}ms)` : ''}` : 'deepslate loading'}
        </div>
      </div>
      <div
        ref={wrapperRef}
        className="pane-body visualizer-canvas-wrap"
        onPointerLeave={() => setHoverData(null)}
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
          try {
            if (viewMode === 'top') {
              const worldZ = panZ + (py - rect.height / 2) / zoom
              const val = sampler(worldX, yLevel, worldZ)
              setHoverData({ x: Math.floor(worldX), z: Math.floor(worldZ), val })
            } else {
              const worldY = panY - (py - rect.height / 2) / zoom
              const val = sampler(worldX, worldY, zLevel)
              setHoverData({ x: Math.floor(worldX), y: Math.floor(worldY), val })
            }
          } catch {
            setHoverData(null)
          }
        }}
        onPointerUp={(event) => {
          dragRef.current = null
          ;(event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId)
        }}
        onWheel={(event) => {
          event.preventDefault()
          const factor = event.deltaY > 0 ? 0.92 : 1.08
          setZoom((value) => Math.min(20, Math.max(0.1, value * factor)))
        }}
      >
        <div className="visualizer-settings-panel" onPointerDown={(e) => e.stopPropagation()} onPointerMove={(e) => e.stopPropagation()} onPointerUp={(e) => e.stopPropagation()} onWheel={(e) => e.stopPropagation()}>
          <div className="visualizer-toolbar">
            <label>View
              <button 
                type="button" 
                onClick={() => setViewMode(v => v === 'top' ? 'side' : 'top')}
                style={{ fontWeight: 600, width: '56px' }}
              >
                {viewMode === 'top' ? 'Top' : 'Side'}
              </button>
            </label>
            <label>Zoom
              <input
                type="range"
                min="0.1"
                max="5"
                step="0.1"
                value={zoom}
                onChange={(event) => setZoom(Number(event.target.value))}
              />
            </label>
            {viewMode === 'top' ? (
              <label>Y
                <input
                  type="range"
                  min="-64"
                  max="320"
                  step="1"
                  value={yLevel}
                  onChange={(event) => setYLevel(Number(event.target.value))}
                />
              </label>
            ) : (
              <label>Z
                <input
                  type="range"
                  min="-1000"
                  max="1000"
                  step="1"
                  value={zLevel}
                  onChange={(event) => setZLevel(Number(event.target.value))}
                />
              </label>
            )}
            <label>Seed
              <div style={{ display: 'flex', gap: '4px' }}>
                <input
                  type="text"
                  value={seedStr}
                  onChange={(event) => setSeedStr(event.target.value)}
                  style={{ width: '80px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', color: 'inherit', padding: '4px 8px', borderRadius: '6px' }}
                />
                <button
                  type="button"
                  onClick={() => setSeedStr(Math.floor(Math.random() * 2147483647).toString())}
                  style={{ padding: '4px 8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                  title="Randomize Seed"
                >🎲</button>
              </div>
            </label>
            <button type="button" onClick={() => { setZoom(2); setPanX(0); setPanY(64); setPanZ(0); setYLevel(64); setZLevel(0); setSeedStr('0'); setViewMode('top') }}>
              Reset
            </button>
          </div>
          <div className="visualizer-settings-handle">
            <span>Hover to open settings</span>
          </div>
        </div>
        <div style={{ position: 'absolute', top: 12, left: 12, padding: '8px 10px', background: 'rgba(0,0,0,0.6)', borderRadius: 6, fontSize: 12, pointerEvents: 'none', color: '#fff' }}>
          <div>Zoom: {zoom.toFixed(2)}x</div>
          <div>{viewMode === 'top' ? `y: ${yLevel.toFixed(0)}` : `z: ${zLevel.toFixed(0)}`}</div>
          {hoverData && (
            <div style={{ marginTop: 4, paddingTop: 4, borderTop: '1px solid rgba(255,255,255,0.2)', color: 'var(--accent2)' }}>
              x: {hoverData.x} {viewMode === 'top' ? `z: ${hoverData.z}` : `y: ${hoverData.y}`}
              <br/>
              𝝆: {Number.isNaN(hoverData.val) ? 'NaN' : hoverData.val.toFixed(5)}
            </div>
          )}
        </div>
        <div style={{ position: 'absolute', bottom: 16, right: 16, pointerEvents: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', filter: 'drop-shadow(0px 1px 2px rgba(0,0,0,0.8))' }}>
          <div style={{
            width: scale.pixels,
            height: 6,
            borderLeft: '2px solid #fff',
            borderRight: '2px solid #fff',
            borderBottom: '2px solid #fff',
            marginBottom: 4
          }} />
          <div style={{
            color: '#fff',
            fontSize: 11,
            fontWeight: 500,
          }}>
            {scale.blocks} blocks
          </div>
        </div>
        <canvas ref={canvasRef} className="visualizer-canvas" />
        {(parseError || runtimeError) && (
          <div style={{
            position: 'absolute',
            bottom: 12,
            left: 12,
            right: 12,
            background: 'var(--danger)',
            color: '#fff',
            padding: '10px 14px',
            borderRadius: '8px',
            fontSize: '13px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
            zIndex: 20,
            pointerEvents: 'none'
          }}>
            <strong>Deepslate Error:</strong> {parseError || runtimeError}
          </div>
        )}
      </div>
    </section>
  )
}
