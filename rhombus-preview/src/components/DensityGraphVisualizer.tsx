import React, { useState, useMemo, useEffect } from 'react';
import { DensityFunction, NoiseGeneratorSettings, NoiseRouter, RandomState, Registry, Identifier } from 'deepslate';
import { loadDeepslateRuntime } from '../lib/deepslate';
import type { RhombusContextFile } from '../types';

export interface DensityGraphVisualizerProps {
  onClose: () => void;
  file: RhombusContextFile;
  contextFiles: RhombusContextFile[];
}

function extractReferences(obj: any, refs = new Set<string>()) {
  if (!obj || typeof obj !== 'object') return refs;
  if (Array.isArray(obj)) {
    obj.forEach(o => extractReferences(o, refs));
    return refs;
  }
  for (const key in obj) {
    if (typeof obj[key] === 'string' && key !== 'type' && key !== 'noise' && key !== 'id') {
      if (/^([a-z0-9_.-]+:)?[a-z0-9_./-]+$/.test(obj[key])) {
        refs.add(obj[key]);
      }
    } else if (typeof obj[key] === 'object') {
      extractReferences(obj[key], refs);
    }
  }
  return refs;
}

// removed replaceReference

function niceNum(range: number, round: boolean): number {
  if (range === 0) return 0;
  const exponent = Math.floor(Math.log10(range));
  const fraction = range / Math.pow(10, exponent);
  let niceFraction;
  if (round) {
    if (fraction < 1.5) niceFraction = 1;
    else if (fraction < 3) niceFraction = 2;
    else if (fraction < 7) niceFraction = 5;
    else niceFraction = 10;
  } else {
    if (fraction <= 1) niceFraction = 1;
    else if (fraction <= 2) niceFraction = 2;
    else if (fraction <= 5) niceFraction = 5;
    else niceFraction = 10;
  }
  return niceFraction * Math.pow(10, exponent);
}

function getNiceTicks(min: number, max: number, maxTicks = 5) {
  if (min === max) {
    return { ticks: [min], niceMin: min - 1, niceMax: min + 1 };
  }
  const range = niceNum(max - min, false);
  const tickSpacing = niceNum(range / (maxTicks - 1), true);
  const niceMin = Math.floor(min / tickSpacing) * tickSpacing;
  const niceMax = Math.ceil(max / tickSpacing) * tickSpacing;
  
  const ticks = [];
  for (let t = niceMin; t <= niceMax + 1e-9; t += tickSpacing) {
    ticks.push(Math.abs(t) < 1e-9 ? 0 : t);
  }
  return { ticks, niceMin, niceMax };
}

export default function DensityGraphVisualizer({ onClose, file, contextFiles }: DensityGraphVisualizerProps) {
  const [selectedRef, setSelectedRef] = useState<string>('');
  const [xMinInput, setXMinInput] = useState<string>('-5');
  const [xMaxInput, setXMaxInput] = useState<string>('5');

  const xMin = Number.isNaN(parseFloat(xMinInput)) ? 0 : parseFloat(xMinInput);
  const xMax = Number.isNaN(parseFloat(xMaxInput)) ? 0 : parseFloat(xMaxInput);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Close modal on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const availableRefs = useMemo(() => {
    try {
      const refs = extractReferences(file.content);
      return Array.from(refs).sort();
    } catch {
      return [];
    }
  }, [file.content]);

  useEffect(() => {
    if (availableRefs.length > 0 && (!selectedRef || !availableRefs.includes(selectedRef))) {
      setSelectedRef(availableRefs[0]);
    }
  }, [availableRefs, selectedRef]);

  const graphData = useMemo(() => {
    if (!selectedRef) return null;
    
    try {
      const runtime = loadDeepslateRuntime();
      runtime.registerFiles(contextFiles);
      
      let dfRegistry: any = null;
      Registry.REGISTRY.forEach((key, registry) => {
          if (key.path === 'worldgen/density_function') {
              dfRegistry = registry;
          }
      });

      let currentX = 0;
      class MockInputFunction extends DensityFunction {
          compute() { return currentX; }
          minValue() { return -Infinity; }
          maxValue() { return Infinity; }
          mapAll(v: any) { return v.map(this); }
      }
      
      if (dfRegistry) {
          try {
              const parsedId = Identifier.parse(selectedRef);
              dfRegistry.register(parsedId, new MockInputFunction());
          } catch (e) {
              console.warn("Failed to register mock reference", e);
          }
      }
      
      const df = DensityFunction.fromJson(file.content);
      const settings = NoiseGeneratorSettings.create({
          noise: { minY: 0, height: 256, xzSize: 1, ySize: 1 },
          noiseRouter: NoiseRouter.create({ finalDensity: df }),
      });

      const points = [];
      const steps = 1000;
      let actualMinY = Infinity;
      let actualMaxY = -Infinity;

      const safeMinX = Math.min(xMin, xMax);
      const safeMaxX = Math.max(xMin, xMax);
      const range = safeMaxX - safeMinX || 1;

      for (let i = 0; i <= steps; i++) {
        currentX = safeMinX + (i / steps) * range;
        
        // Re-create RandomState to clear DensityFunction caches (e.g. cache_once, cache_2d)
        const state = new RandomState(settings, 0n);
        const y = state.router.finalDensity.compute({ x: 0, y: 0, z: 0 });
        
        if (!Number.isNaN(y)) {
          actualMinY = Math.min(actualMinY, y);
          actualMaxY = Math.max(actualMaxY, y);
          points.push({ x: currentX, y });
        }
      }

      if (points.length < 2) {
          setErrorMsg("Graph generated less than 2 valid points.");
          return null;
      }
      setErrorMsg(null);
      return { points, actualMinY, actualMaxY, safeMinX, safeMaxX };
    } catch (e: any) {
      console.error("Failed to generate graph", e);
      setErrorMsg(e.stack || e.message || String(e));
      return null;
    }
  }, [file.content, contextFiles, selectedRef, xMin, xMax]);

  const formatTick = (n: number) => Number.isInteger(n) ? n.toString() : n.toFixed(2).replace(/\.?0+$/, '');

  const svgContent = useMemo(() => {
    if (!graphData) return null;
    const { points, actualMinY, actualMaxY, safeMinX, safeMaxX } = graphData;

    let minX = safeMinX, maxX = safeMaxX;
    let minY = actualMinY, maxY = actualMaxY;
    if (minY === maxY) { minY -= 1; maxY += 1; }
    
    const xTicksObj = getNiceTicks(minX, maxX, 8);
    minX = xTicksObj.niceMin;
    maxX = xTicksObj.niceMax;
    
    const yTicksObj = getNiceTicks(minY, maxY, 6);
    minY = yTicksObj.niceMin;
    maxY = yTicksObj.niceMax;

    const width = 800, height = 400, padX = 60, padTop = 30, padBottom = 40;
    const mapX = (x: number) => padX + ((x - minX) / (maxX - minX)) * (width - padX * 2);
    const mapY = (y: number) => height - padBottom - ((y - minY) / (maxY - minY)) * (height - padTop - padBottom);

    const zeroY = minY <= 0 && maxY >= 0 ? mapY(0) : height - padBottom;
    const zeroX = minX <= 0 && maxX >= 0 ? mapX(0) : padX;

    const xAxisTicks = xTicksObj.ticks.map(t => (
      <text key={`xt_${t}`} x={mapX(t)} y={height - padBottom + 20} fill="#aaa" fontSize="12" fontFamily="sans-serif" textAnchor="middle">{formatTick(t)}</text>
    ));

    const yAxisTicks = yTicksObj.ticks.map(t => (
      <text key={`yt_${t}`} x={padX - 10} y={mapY(t)} fill="#aaa" fontSize="12" fontFamily="sans-serif" textAnchor="end" dominantBaseline="middle">{formatTick(t)}</text>
    ));

    const gridLines = yTicksObj.ticks.map(t => (
      <line key={`gl_${t}`} x1={padX} y1={mapY(t)} x2={width - padX} y2={mapY(t)} stroke="#333" strokeWidth="1" strokeDasharray="4 4" />
    ));

    let pathD = `M ${mapX(points[0].x)} ${mapY(points[0].y)}`;
    for (let i = 1; i < points.length; i++) {
      pathD += ` L ${mapX(points[i].x)} ${mapY(points[i].y)}`;
    }

    return (
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="xMidYMid meet" style={{ background: '#1e1e1e', borderRadius: '8px', border: '1px solid #333' }}>
        {gridLines}
        <line x1={padX} y1={zeroY} x2={width - padX} y2={zeroY} stroke="#555" strokeWidth="1.5" />
        <line x1={zeroX} y1={padTop} x2={zeroX} y2={height - padBottom} stroke="#555" strokeWidth="1.5" />
        <path d={pathD} fill="none" stroke="#35aaf3" strokeWidth="2.5" />
        {xAxisTicks}
        {yAxisTicks}
      </svg>
    );
  }, [graphData]);

  return (
    <div className="density-graph-modal">
      <div className="density-graph-modal-content">
        <div className="density-graph-header">
          <h2>Density Function Graph</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        <div className="density-graph-controls">
          <div className="control-group">
            <label>Reference:</label>
            <select value={selectedRef} onChange={e => setSelectedRef(e.target.value)}>
              {availableRefs.length === 0 && <option value="">No references found</option>}
              {availableRefs.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="control-group">
            <label>X-Min:</label>
            <input type="number" value={xMinInput} onChange={e => setXMinInput(e.target.value)} />
          </div>
          <div className="control-group">
            <label>X-Max:</label>
            <input type="number" value={xMaxInput} onChange={e => setXMaxInput(e.target.value)} />
          </div>
        </div>
        <div className="density-graph-canvas">
          {svgContent || (
            <div className="no-data">
                {errorMsg ? (
                    <div style={{color: '#ff6b6b', whiteSpace: 'pre-wrap', textAlign: 'left', background: '#333', padding: '10px', borderRadius: '4px'}}>
                        <strong>Error:</strong><br/>{errorMsg}
                    </div>
                ) : (
                    "Cannot generate graph. Select a valid reference or check min/max values."
                )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
