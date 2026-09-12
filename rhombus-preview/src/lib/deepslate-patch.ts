import { DensityFunction } from 'deepslate'

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

//======// Patch of DensityFunction.fromJson to globally validate unknown types //===============//
const originalFromJson = DensityFunction.fromJson;

/**
 * Monkey-patches `DensityFunction.fromJson` to intercept and log unknown density function types.
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
