export type SplineValue = number | string | SplineData;

export interface SplinePoint {
  location?: number;
  value?: SplineValue;
  derivative?: number;
}

export interface SplineData {
  type?: string;
  coordinate?: string;
  points?: SplinePoint[];
  spline?: SplineData;
}

function getPossibleValues(val: SplineValue): number[] {
  if (typeof val === 'number') return [val];
  if (typeof val === 'string') throw new Error('REFERENCE');
  
  const splineData = Array.isArray((val as SplineData)?.points) 
    ? (val as SplineData) 
    : (Array.isArray((val as SplineData)?.spline?.points) ? (val as SplineData).spline : null);
    
  if (splineData && splineData.points) {
    let vals: number[] = [];
    for (const p of splineData.points) {
      if (p.value !== undefined) {
        vals.push(...getPossibleValues(p.value));
      }
    }
    return vals;
  }
  return [];
}

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

export function renderSplineSVG(spline: SplineData): { type: 'success', svg: string } | { type: 'error', message: string } | null {
  if (!spline?.points || !Array.isArray(spline.points)) return null;
  
  const points: { x: number, yList: number[], d: number }[] = [];
  
  try {
    for (const p of spline.points) {
      if (typeof p.location === 'number' && p.value !== undefined) {
        const yList = getPossibleValues(p.value);
        if (yList.length === 0) return null;
        points.push({ 
          x: p.location, 
          yList: yList, 
          d: typeof p.derivative === 'number' ? p.derivative : 0 
        });
      }
    }
  } catch (e) {
    if (e instanceof Error && e.message === 'REFERENCE') {
      return { type: 'error', message: '*Cannot preview spline. It contains non-numerical values.*' };
    }
    return null;
  }
  
  if (points.length < 2) return null;
  points.sort((a, b) => a.x - b.x);
  
  const maxBranches = Math.max(...points.map(p => p.yList.length));
  
  let minX = points[0].x, maxX = points[points.length - 1].x;
  let minY = Infinity, maxY = -Infinity;
  for (const p of points) {
    for (const y of p.yList) {
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
    }
  }
  
  if (minX === maxX) { minX -= 1; maxX += 1; }
  if (minY === maxY) { minY -= 1; maxY += 1; }
  
  const xTicksObj = getNiceTicks(minX, maxX, 5);
  minX = xTicksObj.niceMin;
  maxX = xTicksObj.niceMax;
  
  const yTicksObj = getNiceTicks(minY, maxY, 5);
  minY = yTicksObj.niceMin;
  maxY = yTicksObj.niceMax;
  
  const width = 340, height = 205, padX = 40, padTop = 22, padBottom = 26;
  const mapX = (x: number) => padX + ((x - minX) / (maxX - minX)) * (width - padX * 2);
  const mapY = (y: number) => height - padBottom - ((y - minY) / (maxY - minY)) * (height - padTop - padBottom);
  
  let paths = '';
  let circles = '';
  
  for (let b = 0; b < maxBranches; b++) {
    const branchPoints = points.map(p => ({
      x: p.x,
      y: p.yList[Math.min(b, p.yList.length - 1)],
      d: p.d
    }));
    
    let path = `M ${mapX(branchPoints[0].x)} ${mapY(branchPoints[0].y)}`;
    for (let i = 0; i < branchPoints.length - 1; i++) {
      const p0 = branchPoints[i], p1 = branchPoints[i+1];
      const dx = p1.x - p0.x;
      const c0x = p0.x + dx / 3, c0y = p0.y + (dx / 3) * p0.d;
      const c1x = p1.x - dx / 3, c1y = p1.y - (dx / 3) * p1.d;
      path += ` C ${mapX(c0x)} ${mapY(c0y)}, ${mapX(c1x)} ${mapY(c1y)}, ${mapX(p1.x)} ${mapY(p1.y)}`;
    }
    
    const opacity = maxBranches > 1 ? (0.4 + 0.6 * (b / (maxBranches - 1 || 1))) : 1.0;
    paths += `<path d="${path}" fill="none" stroke="#35aaf3" stroke-width="2" opacity="${opacity}" />`;
    circles += branchPoints.map(p => `<circle cx="${mapX(p.x)}" cy="${mapY(p.y)}" r="3" fill="#fff" opacity="${opacity}" />`).join('');
  }
  
  const zeroY = minY <= 0 && maxY >= 0 ? mapY(0) : height - padBottom;
  const zeroX = minX <= 0 && maxX >= 0 ? mapX(0) : padX;
  
  const formatTick = (n: number) => Number.isInteger(n) ? n.toString() : n.toFixed(2).replace(/\.?0+$/, '');

  const xAxisTicks = xTicksObj.ticks.map(t => 
    `<text x="${mapX(t)}" y="${height - padBottom + 15}" fill="#aaa" font-size="10" font-family="sans-serif" text-anchor="middle">${formatTick(t)}</text>`
  ).join('');

  const yAxisTicks = yTicksObj.ticks.map(t => 
    `<text x="${padX-6}" y="${mapY(t)}" fill="#aaa" font-size="10" font-family="sans-serif" text-anchor="end" dominant-baseline="middle">${formatTick(t)}</text>`
  ).join('');

  const gridLines = yTicksObj.ticks.map(t => 
    `<line x1="${padX}" y1="${mapY(t)}" x2="${width-padX}" y2="${mapY(t)}" stroke="#333" stroke-width="1" stroke-dasharray="2 2" />`
  ).join('');
  
  const svg = `
<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg" style="background:#1e1e1e; border-radius:6px; border: 1px solid #333;">
  ${gridLines}
  <line x1="${padX}" y1="${zeroY}" x2="${width-padX}" y2="${zeroY}" stroke="#555" stroke-width="1" />
  <line x1="${zeroX}" y1="${padTop}" x2="${zeroX}" y2="${height-padBottom}" stroke="#555" stroke-width="1" />
  ${paths}
  ${circles}
  ${xAxisTicks}
  ${yAxisTicks}
</svg>
`;
  return { type: 'success', svg: `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg.trim())))}` };
}
