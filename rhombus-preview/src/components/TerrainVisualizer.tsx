import React, { useRef, useMemo, useState, useEffect } from 'react'
import { NoiseGeneratorSettings, RandomState, FixedBiomeSource, Identifier, NoiseChunkGenerator, Chunk, ChunkPos, WorldgenRegistries } from 'deepslate'
import CanvasVisualizer, { ViewState } from './CanvasVisualizer'
import { patchState } from '../lib/deepslate-patch'
import type { RhombusContextFile } from '../types'
import { normalizeRegistryName } from '../lib/registry'

interface TerrainVisualizerProps {
    file: RhombusContextFile
    contextFiles: RhombusContextFile[]
}

const BlockColors: Record<string, [number, number, number]> = {
    'minecraft:air': [167, 191, 214],
    'minecraft:water': [20, 80, 170],
    'minecraft:lava': [200, 100, 0],
    'minecraft:stone': [55, 55, 55],
    'minecraft:deepslate': [34, 34, 36],
    'minecraft:bedrock': [10, 10, 10],
    'minecraft:grass_block': [47, 120, 23],
    'minecraft:dirt': [64, 40, 8],
    'minecraft:gravel': [70, 70, 70],
    'minecraft:sand': [196, 180, 77],
    'minecraft:sandstone': [148, 135, 52],
    'minecraft:netherrack': [100, 40, 40],
    'minecraft:crimson_nylium': [144, 22, 22],
    'minecraft:warped_nylium': [28, 115, 113],
    'minecraft:basalt': [73, 74, 85],
    'minecraft:end_stone': [200, 200, 140],
}

class ChunkCache {
    settings: NoiseGeneratorSettings
    state: RandomState
    generator: NoiseChunkGenerator
    cache: Map<string, Chunk>
    pendingChunks: Set<string>
    viewMode: string
    yLevel: number
    zLevel: number
    onUpdate: () => void
    destroyed: boolean = false
    
    constructor(settings: NoiseGeneratorSettings, seed: bigint, viewMode: string, yLevel: number, zLevel: number, onUpdate: () => void) {
        this.settings = settings
        this.state = new RandomState(settings, seed)
        const biomeSource = new FixedBiomeSource(Identifier.create('minecraft:plains'))
        this.generator = new NoiseChunkGenerator(biomeSource, settings)
        this.cache = new Map()
        this.pendingChunks = new Set()
        this.viewMode = viewMode
        this.yLevel = yLevel
        this.zLevel = zLevel
        this.onUpdate = onUpdate
    }
    
    destroy() {
        this.destroyed = true
        this.cache.clear()
        this.pendingChunks.clear()
    }

    getBlock(x: number, y: number, z: number): string {
        if (this.destroyed) return 'minecraft:air'
        const { minY, height } = this.settings.noise
        if (y < minY || y >= minY + height) {
            return 'minecraft:air'
        }
        
        const cx = Math.floor(x / 16)
        const cz = Math.floor(z / 16)
        const key = `${cx},${cz}`
        
        const chunk = this.cache.get(key)
        if (chunk) {
            try {
                return chunk.getBlockState([x, y, z]).getName().toString()
            } catch {
                return 'minecraft:air'
            }
        }

        if (!this.pendingChunks.has(key)) {
            this.pendingChunks.add(key)
            setTimeout(() => {
                if (this.destroyed) return
                const t0 = performance.now()
                try {
                    const newChunk = new Chunk(minY, height, ChunkPos.create(cx, cz))
                    // Inject patch state to only compute the visible 2D slice
                    if (this.viewMode === 'top') {
                        patchState.targetY = Math.floor(this.yLevel)
                        patchState.targetZ = undefined
                    } else {
                        patchState.targetY = undefined
                        patchState.targetZ = Math.floor(this.zLevel) & 0xF
                    }
                    
                    this.generator.fill(this.state, newChunk, false)
                    if ('buildSurface' in this.generator) {
                        (this.generator as any).buildSurface(this.state, newChunk, 'minecraft:plains')
                    }
                    
                    patchState.targetY = undefined
                    patchState.targetZ = undefined
                    
                    this.cache.set(key, newChunk)
                    const t1 = performance.now()
                    console.log(`[Rhombus Debug] Chunk [${cx}, ${cz}] generated successfully in ${(t1 - t0).toFixed(2)}ms.`)
                } catch (e) {
                    console.error('Failed to generate chunk:', cx, cz, e)
                    this.cache.set(key, new Chunk(minY, height, ChunkPos.create(cx, cz)))
                } finally {
                    this.pendingChunks.delete(key)
                    this.onUpdate()
                }
            }, 0)
        }
        
        return 'loading'
    }
}

export default function TerrainVisualizer({ file, contextFiles }: TerrainVisualizerProps) {
    const registry = normalizeRegistryName(file.registry)
    const [, setTick] = useState(0)
    const forceUpdate = () => setTick(t => t + 1)
    
    const parseResult = useMemo(() => {
        try {
            if (registry === 'worldgen/noise_settings') {
                const settings = NoiseGeneratorSettings.fromJson(file.content)
                return {
                    type: 'terrain',
                    factory: (seed: bigint, viewMode: string, yLevel: number, zLevel: number) => new ChunkCache(settings, seed, viewMode, yLevel, zLevel, forceUpdate)
                }
            }
            return { error: `Unsupported registry for terrain: ${registry}` }
        } catch (err) {
            return { error: err instanceof Error ? err.message : String(err) }
        }
    }, [file.content, registry])

    const cacheRef = useRef<{ seed: bigint, viewMode: string, yLevel: number, zLevel: number, factory: any, cache: ChunkCache } | null>(null)

    useEffect(() => {
        return () => {
            if (cacheRef.current) {
                cacheRef.current.cache.destroy()
            }
        }
    }, [])

    const onDraw = (image: ImageData, viewState: ViewState, onError: (msg: string | null) => void) => {
        if ('error' in parseResult) {
            onError(parseResult.error ?? null)
            return
        }

        if (
            cacheRef.current?.seed !== viewState.seed ||
            cacheRef.current?.viewMode !== viewState.viewMode ||
            cacheRef.current?.yLevel !== viewState.yLevel ||
            cacheRef.current?.zLevel !== viewState.zLevel ||
            cacheRef.current?.factory !== parseResult.factory
        ) {
            cacheRef.current?.cache.destroy()
            cacheRef.current = {
                seed: viewState.seed,
                viewMode: viewState.viewMode,
                yLevel: viewState.yLevel,
                zLevel: viewState.zLevel,
                factory: parseResult.factory,
                cache: parseResult.factory(viewState.seed, viewState.viewMode, viewState.yLevel, viewState.zLevel)
            }
        }
        
        const chunkCache = cacheRef.current.cache
        const { width, height } = image
        const { panX, panY, panZ, zoom, pixelSize, viewMode, yLevel, zLevel } = viewState
        const rectWidth = width * pixelSize
        const rectHeight = height * pixelSize

        for (let py = 0; py < height; py += 1) {
            for (let px = 0; px < width; px += 1) {
                const worldX = panX + (px * pixelSize - rectWidth / 2) / zoom
                
                let blockX = Math.floor(worldX)
                let blockY = 0
                let blockZ = 0
                
                if (viewMode === 'top') {
                    const worldZ = panZ + (py * pixelSize - rectHeight / 2) / zoom
                    blockY = Math.floor(yLevel)
                    blockZ = Math.floor(worldZ)
                } else {
                    const worldY = panY - (py * pixelSize - rectHeight / 2) / zoom
                    blockY = Math.floor(worldY)
                    blockZ = Math.floor(zLevel)
                }
                
                const blockName = chunkCache.getBlock(blockX, blockY, blockZ)
                let color: [number, number, number]
                
                if (blockName === 'loading') {
                    // Checkerboard pattern for loading chunks
                    const isCheck = (Math.floor(px / 4) + Math.floor(py / 4)) % 2 === 0
                    color = isCheck ? [230, 230, 230] : [200, 200, 200]
                } else {
                    color = BlockColors[blockName] || [255, 0, 255] // magenta for unknown
                }
                
                const offset = (py * width + px) * 4
                image.data[offset] = color[0]
                image.data[offset + 1] = color[1]
                image.data[offset + 2] = color[2]
                image.data[offset + 3] = 255
            }
        }
    }

    const renderTooltip = (viewState: ViewState, worldX: number, worldY: number, worldZ: number) => {
        if ('error' in parseResult) return null
        
        if (
            cacheRef.current?.seed !== viewState.seed ||
            cacheRef.current?.viewMode !== viewState.viewMode ||
            cacheRef.current?.yLevel !== viewState.yLevel ||
            cacheRef.current?.zLevel !== viewState.zLevel ||
            cacheRef.current?.factory !== parseResult.factory
        ) {
            cacheRef.current?.cache.destroy()
            cacheRef.current = {
                seed: viewState.seed,
                viewMode: viewState.viewMode,
                yLevel: viewState.yLevel,
                zLevel: viewState.zLevel,
                factory: parseResult.factory,
                cache: parseResult.factory(viewState.seed, viewState.viewMode, viewState.yLevel, viewState.zLevel)
            }
        }
        
        const chunkCache = cacheRef.current.cache
        const bx = Math.floor(worldX)
        const by = Math.floor(worldY)
        const bz = Math.floor(worldZ)
        const blockName = chunkCache.getBlock(bx, by, bz)
        
        return (
            <>
                x: {bx} y: {by} z: {bz}
                <br/>
                Block: <strong>{blockName === 'loading' ? 'Lade Chunk...' : blockName}</strong>
            </>
        )
    }

    return (
        <CanvasVisualizer
            file={file}
            contextFiles={contextFiles}
            parseError={'error' in parseResult ? (parseResult.error ?? null) : null}
            onDraw={onDraw}
            renderTooltip={renderTooltip}
        />
    )
}
