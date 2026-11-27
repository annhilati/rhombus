/**
 * TEMPORARY PATCH: upscale
 * Introduced in Minecraft Java Edition 26.4 (renamed from `interpolated`) / version 125+.
 * 
 * Samples an input density function at a reduced resolution and upscales across X, Z, and Y axes.
 * Supports the 5 vanilla interpolation modes:
 * - nearest_neighbor (1 sample)
 * - interpolate_linear (2 samples)
 * - interpolate_cosine (2 samples)
 * - interpolate_cubic (4 samples, Catmull-Rom spline)
 * - b_spline_cubic (4 samples, B-spline approximation)
 */

import { DensityFunction, Interval } from 'deepslate';

export type UpscaleMode =
  | 'nearest_neighbor'
  | 'interpolate_linear'
  | 'interpolate_cosine'
  | 'interpolate_cubic'
  | 'b_spline_cubic';

export interface AxisScaling {
  mode: UpscaleMode;
  cellSize: number;
}

interface ModeInfo {
  samplesBefore: number;
  samplesAfter: number;
  sampleCount: number;
  exactValueOnVertex: boolean;
}

const MODE_INFOS: Record<UpscaleMode, ModeInfo> = {
  nearest_neighbor: { samplesBefore: 0, samplesAfter: 0, sampleCount: 1, exactValueOnVertex: true },
  interpolate_linear: { samplesBefore: 0, samplesAfter: 1, sampleCount: 2, exactValueOnVertex: true },
  interpolate_cosine: { samplesBefore: 0, samplesAfter: 1, sampleCount: 2, exactValueOnVertex: true },
  interpolate_cubic: { samplesBefore: 1, samplesAfter: 2, sampleCount: 4, exactValueOnVertex: true },
  b_spline_cubic: { samplesBefore: 1, samplesAfter: 2, sampleCount: 4, exactValueOnVertex: false },
};

function computeCoefficients(mode: UpscaleMode, alpha: number): number[] {
  switch (mode) {
    case 'nearest_neighbor':
      return [1.0];

    case 'interpolate_linear':
      return [1.0 - alpha, alpha];

    case 'interpolate_cosine': {
      // Ease.inOutSine(alpha) = (1.0 - Math.cos(Math.PI * alpha)) / 2.0
      const a = (1.0 - Math.cos(Math.PI * alpha)) / 2.0;
      return [1.0 - a, a];
    }

    case 'interpolate_cubic': {
      const a = alpha;
      const a2 = a * a;
      const a3 = a2 * a;
      return [
        -0.5 * a3 + a2 - 0.5 * a,
        1.5 * a3 - 2.5 * a2 + 1.0,
        -1.5 * a3 + 2.0 * a2 + 0.5 * a,
        0.5 * a3 - 0.5 * a2,
      ];
    }

    case 'b_spline_cubic': {
      const a = alpha;
      const a2 = a * a;
      const a3 = a2 * a;
      const oneMinusA = 1.0 - a;
      const oneMinusA3 = oneMinusA * oneMinusA * oneMinusA;
      return [
        oneMinusA3 / 6.0,
        (3.0 * a3 - 6.0 * a2 + 4.0) / 6.0,
        (-3.0 * a3 + 3.0 * a2 + 3.0 * a + 1.0) / 6.0,
        a3 / 6.0,
      ];
    }
  }
}

function computeCoefficientsTable(cellSize: number, mode: UpscaleMode): number[][] {
  const table: number[][] = new Array(cellSize);
  for (let i = 0; i < cellSize; i += 1) {
    table[i] = computeCoefficients(mode, i / cellSize);
  }
  return table;
}

function floorMod(n: number, m: number): number {
  return ((n % m) + m) % m;
}

export class Upscale extends DensityFunction {
  readonly input: DensityFunction;
  readonly x: AxisScaling;
  readonly y: AxisScaling;
  readonly z: AxisScaling;

  private readonly coeffTableX: number[][];
  private readonly coeffTableY: number[][];
  private readonly coeffTableZ: number[][];
  private readonly modeInfoX: ModeInfo;
  private readonly modeInfoY: ModeInfo;
  private readonly modeInfoZ: ModeInfo;

  private readonly values: Map<string, number> = new Map();

  constructor(
    input: DensityFunction,
    x: AxisScaling = { mode: 'interpolate_linear', cellSize: 4 },
    y: AxisScaling = { mode: 'interpolate_linear', cellSize: 8 },
    z: AxisScaling = { mode: 'interpolate_linear', cellSize: 4 }
  ) {
    super();
    this.input = input;
    this.x = { mode: x.mode, cellSize: Math.max(1, Math.min(64, Math.floor(x.cellSize))) };
    this.y = { mode: y.mode, cellSize: Math.max(1, Math.min(64, Math.floor(y.cellSize))) };
    this.z = { mode: z.mode, cellSize: Math.max(1, Math.min(64, Math.floor(z.cellSize))) };

    this.modeInfoX = MODE_INFOS[this.x.mode] ?? MODE_INFOS.interpolate_linear;
    this.modeInfoY = MODE_INFOS[this.y.mode] ?? MODE_INFOS.interpolate_linear;
    this.modeInfoZ = MODE_INFOS[this.z.mode] ?? MODE_INFOS.interpolate_linear;

    this.coeffTableX = computeCoefficientsTable(this.x.cellSize, this.x.mode);
    this.coeffTableY = computeCoefficientsTable(this.y.cellSize, this.y.mode);
    this.coeffTableZ = computeCoefficientsTable(this.z.cellSize, this.z.mode);
  }

  private computeCorner(x: number, y: number, z: number): number {
    const key = `${x} ${y} ${z}`;
    let val = this.values.get(key);
    if (val === undefined) {
      if (this.values.size > 16384) {
        this.values.clear();
      }
      val = this.input.compute(DensityFunction.context(x, y, z));
      this.values.set(key, val);
    }
    return val;
  }

  compute(context: DensityFunction.Context): number {
    const blockX = context.x;
    const blockY = context.y;
    const blockZ = context.z;

    const xInCell = floorMod(blockX, this.x.cellSize);
    const yInCell = floorMod(blockY, this.y.cellSize);
    const zInCell = floorMod(blockZ, this.z.cellSize);

    // Fast-path: exactly on cell vertices
    if (
      xInCell === 0 &&
      yInCell === 0 &&
      zInCell === 0 &&
      this.modeInfoX.exactValueOnVertex &&
      this.modeInfoY.exactValueOnVertex &&
      this.modeInfoZ.exactValueOnVertex
    ) {
      return this.computeCorner(blockX, blockY, blockZ);
    }

    const minSampleX = blockX - xInCell - this.modeInfoX.samplesBefore * this.x.cellSize;
    const minSampleY = blockY - yInCell - this.modeInfoY.samplesBefore * this.y.cellSize;
    const minSampleZ = blockZ - zInCell - this.modeInfoZ.samplesBefore * this.z.cellSize;

    const countX = this.modeInfoX.sampleCount;
    const countY = this.modeInfoY.sampleCount;
    const countZ = this.modeInfoZ.sampleCount;

    const cX = this.coeffTableX[xInCell];
    const cY = this.coeffTableY[yInCell];
    const cZ = this.coeffTableZ[zInCell];

    // Separable 3D interpolation in Minecraft order: X, then Z, then Y
    // Step 1: Interpolate along X for each (y, z)
    // samplesX[sz * countY + sy]
    const samplesX = new Float64Array(countZ * countY);
    for (let sz = 0; sz < countZ; sz += 1) {
      const sampleZ = minSampleZ + sz * this.z.cellSize;
      for (let sy = 0; sy < countY; sy += 1) {
        const sampleY = minSampleY + sy * this.y.cellSize;
        let sumX = 0;
        for (let sx = 0; sx < countX; sx += 1) {
          const sampleX = minSampleX + sx * this.x.cellSize;
          const cornerVal = this.computeCorner(sampleX, sampleY, sampleZ);
          sumX += cX[sx] * cornerVal;
        }
        samplesX[sz * countY + sy] = sumX;
      }
    }

    // Step 2: Interpolate along Z for each y
    // samplesZ[sy]
    const samplesZ = new Float64Array(countY);
    for (let sy = 0; sy < countY; sy += 1) {
      let sumZ = 0;
      for (let sz = 0; sz < countZ; sz += 1) {
        sumZ += cZ[sz] * samplesX[sz * countY + sy];
      }
      samplesZ[sy] = sumZ;
    }

    // Step 3: Interpolate along Y
    let finalValue = 0;
    for (let sy = 0; sy < countY; sy += 1) {
      finalValue += cY[sy] * samplesZ[sy];
    }

    return finalValue;
  }

  mapChildren(visitor: DensityFunction.Visitor): DensityFunction {
    return new Upscale(visitor.apply(this.input), this.x, this.y, this.z);
  }

  range(): Interval {
    return this.input.range();
  }

  static fromJson(obj: unknown, inputParser?: (obj: unknown) => DensityFunction): Upscale {
    const parser = typeof inputParser === 'function' ? inputParser : DensityFunction.fromJson;
    const root = (typeof obj === 'object' && obj !== null) ? (obj as any) : {};

    const input = root.input !== undefined
      ? parser(root.input)
      : root.argument !== undefined
      ? parser(root.argument)
      : DensityFunction.Constant.ZERO;

    const parseAxis = (axisObj: any, fallbackCellSize: number): AxisScaling => {
      const mode = (axisObj?.mode as UpscaleMode) ?? 'interpolate_linear';
      const cellSize = Number(axisObj?.cell_size ?? fallbackCellSize) || fallbackCellSize;
      return { mode, cellSize };
    };

    const fallbackXz = Number(root.cell_size_xz) || 4;
    const fallbackY = Number(root.cell_size_y) || 8;

    const x = parseAxis(root.x, fallbackXz);
    const y = parseAxis(root.y, fallbackY);
    const z = parseAxis(root.z, fallbackXz);

    return new Upscale(input, x, y, z);
  }
}

// Expose onto DensityFunction namespace
(DensityFunction as any).Upscale = Upscale;
