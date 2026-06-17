import { useEffect, useRef, useState } from 'react'
import type { ContextFile } from '../types'
import { getVisualizationKind, normalizeRegistryName } from '../lib/registry'
import { loadDeepslateRuntime } from '../lib/deepslate'
import { DensityFunction, NoiseGeneratorSettings, NoiseParameters, NoiseRouter, NormalNoise, RandomState, XoroshiroRandom, clampedMap } from 'deepslate'
import { viridis } from '../lib/colormap'

interface VisualizerPaneProps {
  file: ContextFile
  allFiles: ContextFile[]
}

function drawCanvas(
  canvas: HTMLCanvasElement,
  file: ContextFile,
  zoom: number,
  panX: number,
  panZ: number,
  yLevel: number,
  seed: bigint
) {
  const pixelSize = 2
  const rect = canvas.getBoundingClientRect()
  const width = Math.max(1, Math.floor(rect.width / pixelSize))
  const height = Math.max(1, Math.floor(rect.height / pixelSize))
  if (canvas.width !== width) canvas.width = width
  if (canvas.height !== height) canvas.height = height

  const ctx2d = canvas.getContext('2d')
  if (!ctx2d) return

  let sampler: (x: number, y: number, z: number) => number = () => 0
  let asColor: (n: number) => [number, number, number] = () => [0, 0, 0]

  const normalized = normalizeRegistryName(file.registry)

  try {
    if (normalized === 'minecraft:density_function') {
      const settings = NoiseGeneratorSettings.create({
        noise: { minY: 0, height: 256, xzSize: 1, ySize: 1 },
        noiseRouter: NoiseRouter.create({
          finalDensity: DensityFunction.fromJson(file.content),
        }),
      })
      const state = new RandomState(settings, seed)
      const df = state.router.finalDensity
      sampler = (x, y, z) => df.compute({ x, y, z })
      asColor = (n) => {
        const clamped = clampedMap(n, -1, 1, 1, 0)
        const col = viridis(clamped <= 0.5 ? clamped - 0.05 : clamped + 0.05)
        return [col[0] * 255, col[1] * 255, col[2] * 255]
      }
    } else if (normalized === 'minecraft:noise') {
      const random = XoroshiroRandom.create(seed)
      const params = NoiseParameters.fromJson(file.content)
      const noise = new NormalNoise(random, params)
      sampler = (x, y, z) => noise.sample(x, y, z)
      asColor = (n) => {
        const col = viridis(clampedMap(n, -1, 1, 0, 1))
        return [col[0] * 255, col[1] * 255, col[2] * 255]
      }
    }
  } catch (err) {
    console.error('Error creating deepslate sampler:', err)
  }

  const image = ctx2d.createImageData(width, height)

  for (let py = 0; py < height; py += 1) {
    for (let px = 0; px < width; px += 1) {
      const worldX = panX + (px * pixelSize - rect.width / 2) / zoom
      const worldZ = panZ + (py * pixelSize - rect.height / 2) / zoom
      
      const sample = sampler(worldX, yLevel, worldZ)
      const color = asColor(sample)
      
      const offset = (py * width + px) * 4
      image.data[offset] = color[0]
      image.data[offset + 1] = color[1]
      image.data[offset + 2] = color[2]
      image.data[offset + 3] = 255
    }
  }

  ctx2d.putImageData(image, 0, 0)

  ctx2d.fillStyle = 'rgba(0, 0, 0, 0.45)'
  ctx2d.fillRect(12, 12, 225, 74)
  ctx2d.fillStyle = '#fff'
  ctx2d.font = '12px sans-serif'
  ctx2d.fillText(`zoom ${zoom.toFixed(2)}x`, 24, 32)
  ctx2d.fillText(`y ${yLevel.toFixed(0)}`, 24, 52)
  ctx2d.fillText('wheel = zoom, drag = pan', 24, 72)
}

export default function VisualizerPane({ file, allFiles }: VisualizerPaneProps) {
  const kind = getVisualizationKind(file.registry)
  const wrapperRef = useRef<HTMLDivElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [zoom, setZoom] = useState(2)
  const [panX, setPanX] = useState(0)
  const [panZ, setPanZ] = useState(0)
  const [yLevel, setYLevel] = useState(64)
  const [runtimeReady, setRuntimeReady] = useState(false)
  const dragRef = useRef<{ active: boolean; x: number; z: number } | null>(null)
  const seed = 12345n

  useEffect(() => {
    let cancelled = false
    const runtime = loadDeepslateRuntime()
    runtime.registerAllFiles(allFiles)
    if (!cancelled) setRuntimeReady(true)
    return () => {
      cancelled = true
    }
  }, [allFiles])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || kind === null || !runtimeReady) return

    const update = () => drawCanvas(canvas, file, zoom, panX, panZ, yLevel, seed)
    update()

    const observer = new ResizeObserver(update)
    if (wrapperRef.current) observer.observe(wrapperRef.current)

    return () => observer.disconnect()
  }, [file, runtimeReady, zoom, panX, panZ, yLevel, kind])

  if (kind === null) return null

  return (
    <section className="pane pane-visualizer">
      <div className="pane-header">
        <div className="pane-title">Visualization</div>
        <div className="pane-meta">
          {normalizeRegistryName(file.registry)} · {runtimeReady ? 'deepslate ready' : 'deepslate loading'}
        </div>
      </div>
      <div className="visualizer-toolbar">
        <label>
          Zoom
          <input
            type="range"
            min="0.1"
            max="20"
            step="0.1"
            value={zoom}
            onChange={(event) => setZoom(Number(event.target.value))}
          />
        </label>
        <label>
          Y
          <input
            type="range"
            min="-64"
            max="320"
            step="1"
            value={yLevel}
            onChange={(event) => setYLevel(Number(event.target.value))}
          />
        </label>
        <button type="button" onClick={() => { setZoom(2); setPanX(0); setPanZ(0); setYLevel(64) }}>
          Reset
        </button>
      </div>
      <div
        ref={wrapperRef}
        className="pane-body visualizer-canvas-wrap"
        onPointerDown={(event) => {
          dragRef.current = { active: true, x: event.clientX, z: event.clientY }
          ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
        }}
        onPointerMove={(event) => {
          const drag = dragRef.current
          if (!drag?.active) return
          const dx = event.clientX - drag.x
          const dz = event.clientY - drag.z
          dragRef.current = { active: true, x: event.clientX, z: event.clientY }
          setPanX((value) => value - dx / zoom)
          setPanZ((value) => value - dz / zoom)
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
        <canvas ref={canvasRef} className="visualizer-canvas" />
      </div>
    </section>
  )
}
