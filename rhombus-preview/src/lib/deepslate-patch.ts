import { DensityFunction, Interval } from 'deepslate'
import { DomainWarp } from './domain-warp'
import { Upscale } from './upscale'

export { DomainWarp } from './domain-warp'
export { Upscale } from './upscale'

/**
 * Global state for collecting Deepslate parsing errors that do not throw exceptions.
 * It tracks the currently parsed file ID so that nested unknown types can be correctly attributed.
 */
export const patchState = {
  errors: [] as { fileId: string, error: string }[],
  currentFile: null as string | null,
  targetY: undefined as number | undefined,
  targetZ: undefined as number | undefined
};

/**
 * Fixed implementation of IntervalSelect for Deepslate.
 * Deepslate's built-in IntervalSelect has a bug where it slices `functions` to `Math.min(thresholds.length, functions.length)`.
 * However, in Minecraft density functions, an interval_select with N thresholds always expects N + 1 functions
 * (one for each interval: (-inf, t0), [t0, t1), ..., [t_n-1, inf)).
 * Slicing functions to thresholds.length drops the last function, causing it to return a constant value.
 */
export class FixedIntervalSelect extends DensityFunction {
  input: DensityFunction;
  thresholds: number[];
  functions: DensityFunction[];

  constructor(input: DensityFunction, thresholds: number[], functions: DensityFunction[]) {
    super();
    this.input = input;
    const count = Math.min(thresholds.length, Math.max(0, functions.length - 1));
    this.thresholds = thresholds.slice(0, count);
    this.functions = functions.slice(0, count + 1);
  }

  compute(context: any): number {
    const input = this.input.compute(context);
    for (let i = 0; i < this.thresholds.length; i += 1) {
      if (input < this.thresholds[i]) {
        return this.functions[i].compute(context);
      }
    }
    return this.functions[this.functions.length - 1].compute(context);
  }

  mapChildren(visitor: any): DensityFunction {
    return new FixedIntervalSelect(visitor.apply(this.input), this.thresholds, this.functions.map((f: any) => visitor.apply(f)));
  }

  range(): Interval {
    return Interval.encapsulating(...this.functions.map((fn: any) => fn.range()));
  }
}

(DensityFunction as any).IntervalSelect = FixedIntervalSelect;

//======// Patch of DensityFunction.fromJson to globally validate unknown types //===============//
const originalFromJson = DensityFunction.fromJson;

/**
 * Monkey-patches `DensityFunction.fromJson` to intercept unknown density function types
 * and fix buggy built-ins like `interval_select`.
 */
DensityFunction.fromJson = function (obj: unknown, inputParser?: (obj: unknown) => DensityFunction): DensityFunction {
  const parserToUse = typeof inputParser === 'function' ? inputParser : DensityFunction.fromJson;

  if (typeof obj === 'object' && obj !== null && 'type' in obj) {
    const typeStr = (obj as any).type;
    if (typeof typeStr === 'string') {
      const typeId = typeStr.replace(/^minecraft:/, '');
      if (typeId === 'interval_select') {
        const root = obj as any;
        const thresholds = Array.isArray(root.thresholds) ? root.thresholds.map((e: any) => Number(e) || 0) : [];
        const functions = Array.isArray(root.functions) ? root.functions.map((fn: any) => parserToUse(fn)) : [];
        return new FixedIntervalSelect(parserToUse(root.input), thresholds, functions);
      } else if (typeId === 'domain_warp') {
        return DomainWarp.fromJson(obj, parserToUse);
      } else if (typeId === 'upscale') {
        return Upscale.fromJson(obj, parserToUse);
      }
    }
  }

  const result = originalFromJson.call(this, obj, parserToUse);
  
  if (typeof obj === 'object' && obj !== null && 'type' in obj) {
    const typeStr = (obj as any).type;
    if (typeof typeStr === 'string') {
      const typeId = typeStr.replace(/^minecraft:/, '');
      if (result === DensityFunction.Constant.ZERO && typeId !== 'constant') {
        if (patchState.currentFile) {
          patchState.errors.push({ fileId: patchState.currentFile, error: `Unknown density function type: ${typeStr}` });
        }
      }
    }
  }
  return result;
};
