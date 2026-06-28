import { DensityFunction } from 'deepslate'


/**
 * Global state for collecting Deepslate parsing errors that do not throw exceptions.
 * It tracks the currently parsed file ID so that nested unknown types can be correctly attributed.
 */
export const patchState = {
  errors: [] as { fileId: string, error: string }[],
  currentFile: null as string | null
};

//======// Patch of DensityFunction.fromJson to globally validate unknown types //===============//
const originalFromJson = DensityFunction.fromJson;

/**
 * Monkey-patches `DensityFunction.fromJson` to intercept and log unknown density function types.
 * Deepslate normally defaults unknown types to `Constant.ZERO`, which suppresses errors.
 * This patch detects that behavior and records it in `patchState.errors`.
 */
DensityFunction.fromJson = function (obj: unknown, inputParser?: (obj: unknown) => DensityFunction): DensityFunction {
  const parserToUse = inputParser ?? DensityFunction.fromJson;
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


//======// Patch of Ap2.compute to correctly propagate non-finite values in arithmetic //========//
const originalAp2Compute = DensityFunction.Ap2.prototype.compute

/**
 * Monkey-patches arithmetic density functions (add, mul) to bypass constant-folding short-circuits.
 * Deepslate normally assumes `x * 0 = 0`, but if `x` is NaN or Infinity, this is incorrect in JS.
 */
DensityFunction.Ap2.prototype.compute = function (context) {
  if (this.type === 'mul' || this.type === 'add') {
    const isArg1Const = this.argument1 instanceof DensityFunction.Constant
    const isArg2Const = this.argument2 instanceof DensityFunction.Constant

    if (isArg1Const || isArg2Const) {
      const dynamicArg = isArg1Const ? this.argument2 : this.argument1
      const constArg = isArg1Const ? this.argument1 : this.argument2

      const innerResult = dynamicArg.compute(context)
      const constValue = constArg.compute(context)

      if (this.type === 'mul') {
        return innerResult * constValue
      } else {
        return innerResult + constValue
      }
    }
  }

  return originalAp2Compute.call(this, context)
}
