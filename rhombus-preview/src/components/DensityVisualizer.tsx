import React, { useRef, useMemo } from 'react'
import { DensityFunction, NoiseGeneratorSettings, NoiseParameters, NoiseRouter, NormalNoise, RandomState, XoroshiroRandom, clampedMap } from 'deepslate'
import CanvasVisualizer, { ViewState } from './CanvasVisualizer'
import type { RhombusContextFile } from '../types'
import { viridis } from '../lib/colormap'
import { normalizeRegistryName } from '../lib/registry'

interface DensityVisualizerProps {
    file: RhombusContextFile
    contextFiles: RhombusContextFile[]
}

export default function DensityVisualizer({ file, contextFiles }: DensityVisualizerProps) {
    const registry = normalizeRegistryName(file.registry)

    const parseResult = useMemo(() => {
        try {
            if (registry === 'worldgen/density_function') {
                const df = DensityFunction.fromJson(file.content)
                
                // Dry run to catch missing references
                const testSettings = NoiseGeneratorSettings.create({
                    noise: { minY: 0, height: 256, xzSize: 1, ySize: 1 },
                    noiseRouter: NoiseRouter.create({ finalDensity: df }),
                })
                new RandomState(testSettings, 0n)

                return {
                    type: 'density',
                    factory: (seed: bigint) => {
                        const settings = NoiseGeneratorSettings.create({
                            noise: { minY: 0, height: 256, xzSize: 1, ySize: 1 },
                            noiseRouter: NoiseRouter.create({ finalDensity: df }),
                        })
                        const state = new RandomState(settings, seed)
                        return (x: number, y: number, z: number) => state.router.finalDensity.compute({ x, y, z })
                    },
                    asColor: (n: number) => {
                        const clamped = clampedMap(n, -1, 1, 1, 0)
                        const col = viridis(clamped <= 0.5 ? clamped - 0.05 : clamped + 0.05)
                        return [col[0] * 255, col[1] * 255, col[2] * 255]
                    }
                }
            } else if (registry === 'worldgen/noise') {
                const params = NoiseParameters.fromJson(file.content)

                // Dry run to catch errors
                new NormalNoise(XoroshiroRandom.create(0n), params)

                return {
                    type: 'noise',
                    factory: (seed: bigint) => {
                        const random = XoroshiroRandom.create(seed)
                        const noise = new NormalNoise(random, params)
                        return (x: number, y: number, z: number) => noise.sample(x, y, z)
                    },
                    asColor: (n: number) => {
                        const col = viridis(clampedMap(n, -1, 1, 0, 1))
                        return [col[0] * 255, col[1] * 255, col[2] * 255]
                    }
                }
            }
            return { error: `Unsupported registry: ${registry}` }
        } catch (err) {
            return { error: err instanceof Error ? err.message : String(err) }
        }
    }, [file.content, registry, contextFiles])

    const samplerCache = useRef<{ seed: bigint; factory: any; sampler: (x: number, y: number, z: number) => number } | null>(null)

    const onDraw = (image: ImageData, viewState: ViewState, onError: (msg: string | null) => void) => {
        if ('error' in parseResult) {
            onError(parseResult.error ?? null)
            return
        }

        if (
            samplerCache.current?.seed !== viewState.seed ||
            samplerCache.current?.factory !== parseResult.factory
        ) {
            samplerCache.current = {
                seed: viewState.seed,
                factory: parseResult.factory,
                sampler: parseResult.factory(viewState.seed)
            }
        }
        
        const sampler = samplerCache.current.sampler
        const { width, height } = image
        const { panX, panY, panZ, zoom, pixelSize, viewMode, yLevel, zLevel } = viewState
        const rectWidth = width * pixelSize
        const rectHeight = height * pixelSize

        for (let py = 0; py < height; py += 1) {
            for (let px = 0; px < width; px += 1) {
                const worldX = panX + (px * pixelSize - rectWidth / 2) / zoom
                
                try {
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
                    
                    const sample = sampler(blockX, blockY, blockZ)
                    const color = Number.isNaN(sample) ? [128, 128, 128] : parseResult.asColor(sample)
                    
                    const offset = (py * width + px) * 4
                    image.data[offset] = color[0]
                    image.data[offset + 1] = color[1]
                    image.data[offset + 2] = color[2]
                    image.data[offset + 3] = 255
                } catch (err) {
                    onError(err instanceof Error ? err.message : String(err))
                    return
                }
            }
        }
    }

    const renderTooltip = (viewState: ViewState, worldX: number, worldY: number, worldZ: number) => {
        if ('error' in parseResult) return null
        
        if (
            samplerCache.current?.seed !== viewState.seed ||
            samplerCache.current?.factory !== parseResult.factory
        ) {
            samplerCache.current = {
                seed: viewState.seed,
                factory: parseResult.factory,
                sampler: parseResult.factory(viewState.seed)
            }
        }
        
        const sampler = samplerCache.current.sampler
        try {
            const bx = Math.floor(worldX)
            const by = Math.floor(worldY)
            const bz = Math.floor(worldZ)
            const val = sampler(bx, by, bz)
            return (
                <>
                    x: {bx} y: {by} z: {bz}
                    <br/>
                    𝝆: {Number.isNaN(val) ? 'NaN' : val.toFixed(5)}
                </>
            )
        } catch {
            return null
        }
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
