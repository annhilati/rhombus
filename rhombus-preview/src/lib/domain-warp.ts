/**
 * TEMPORARY PATCH: domain_warp
 * Introduced in Minecraft Java Edition 26.5-snap6 (technical snapshot) / version 125.1.
 * 
 * Samples an input density function after applying dynamic coordinate offsets (domain warping).
 * Coordinates are shifted along the X, Y, and Z axes according to the provided offset density functions.
 * Offset results are implicitly truncated to integers (matching Java's (int) cast behavior).
 */

import { DensityFunction, Interval } from 'deepslate';

/**
 * Truncates a floating-point value to a 32-bit integer, matching Java's `(int) doubleValue` cast:
 * - NaN -> 0
 * - >= Integer.MAX_VALUE -> 2147483647
 * - <= Integer.MIN_VALUE -> -2147483648
 * - Otherwise truncated towards zero (Math.trunc)
 */
function toJavaInt(val: number): number {
  if (Number.isNaN(val)) return 0;
  if (val >= 2147483647) return 2147483647;
  if (val <= -2147483648) return -2147483648;
  const rounded = Math.round(val);
  if (Math.abs(val - rounded) < 1e-5) {
    return rounded;
  }
  return Math.trunc(val);
}

export class DomainWarp extends DensityFunction {
  readonly input: DensityFunction;
  readonly offsetX: DensityFunction;
  readonly offsetY: DensityFunction;
  readonly offsetZ: DensityFunction;

  constructor(
    input: DensityFunction,
    offsetX: DensityFunction = DensityFunction.Constant.ZERO,
    offsetY: DensityFunction = DensityFunction.Constant.ZERO,
    offsetZ: DensityFunction = DensityFunction.Constant.ZERO
  ) {
    super();
    this.input = input;
    this.offsetX = offsetX;
    this.offsetY = offsetY;
    this.offsetZ = offsetZ;
  }

  compute(context: DensityFunction.Context): number {
    const ox = this.offsetX.compute(context);
    const oy = this.offsetY.compute(context);
    const oz = this.offsetZ.compute(context);

    const dx = toJavaInt(ox);
    const dy = toJavaInt(oy);
    const dz = toJavaInt(oz);

    const warpedContext: DensityFunction.Context = {
      ...context,
      x: context.x + dx,
      y: context.y + dy,
      z: context.z + dz,
    };

    return this.input.compute(warpedContext);
  }

  mapChildren(visitor: DensityFunction.Visitor): DensityFunction {
    return new DomainWarp(
      visitor.apply(this.input),
      visitor.apply(this.offsetX),
      visitor.apply(this.offsetY),
      visitor.apply(this.offsetZ)
    );
  }

  range(): Interval {
    return this.input.range();
  }

  static fromJson(obj: unknown, inputParser?: (obj: unknown) => DensityFunction): DomainWarp {
    const parser = typeof inputParser === 'function' ? inputParser : DensityFunction.fromJson;
    const root = (typeof obj === 'object' && obj !== null) ? (obj as any) : {};
    const input = root.input !== undefined ? parser(root.input) : DensityFunction.Constant.ZERO;
    const offsetX = root.offset_x !== undefined ? parser(root.offset_x) : DensityFunction.Constant.ZERO;
    const offsetY = root.offset_y !== undefined ? parser(root.offset_y) : DensityFunction.Constant.ZERO;
    const offsetZ = root.offset_z !== undefined ? parser(root.offset_z) : DensityFunction.Constant.ZERO;
    return new DomainWarp(input, offsetX, offsetY, offsetZ);
  }
}

// Expose onto DensityFunction namespace for compatibility with other deepslate constructs
(DensityFunction as any).DomainWarp = DomainWarp;
