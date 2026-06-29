import { DensityFunction, NoiseChunk, BlockState, SurfaceSystem, ChunkPos, SurfaceContext, BlockPos } from 'deepslate'


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

//======// Patch of NoiseChunk.getFinalState to optimize chunk generation //=================//
const originalGetFinalState = NoiseChunk.prototype.getFinalState;

NoiseChunk.prototype.getFinalState = function (x: number, y: number, z: number) {
  if (patchState.targetY !== undefined && y !== patchState.targetY) return BlockState.AIR;
  if (patchState.targetZ !== undefined && (z & 0xF) !== patchState.targetZ) return BlockState.AIR;
  return originalGetFinalState.call(this, x, y, z);
}

//======// Patch of SurfaceSystem.buildSurface to fix 3D artifacts //========================//
// Deepslate 0.26.0 hardcodes `for (let z = 0; z < 1; z += 1)` in buildSurface!
// This was an optimization for 2D visualizers, but it completely breaks 3D terrain by
// only applying surface rules to a single slice per chunk, causing sharp edges and floating islands.
SurfaceSystem.prototype.buildSurface = function (chunk: any, noiseChunk: any, worldgenContext: any, getBiome: any) {
  const minX = ChunkPos.minBlockX(chunk.pos);
  const minZ = ChunkPos.minBlockZ(chunk.pos);
  const surfaceContext = new SurfaceContext(this, chunk, noiseChunk, worldgenContext, getBiome);
  const ruleWithContext = (this as any).rule(surfaceContext);

  for (let x = 0; x < 16; x += 1) {
      const worldX = minX + x;
      // FIX: Loop up to 16 instead of 1!
      for (let z = 0; z < 16; z += 1) {
          if (patchState.targetZ !== undefined && z !== patchState.targetZ) continue;
          
          const worldZ = minZ + z;
          surfaceContext.updateXZ(worldX, worldZ);
          let stoneDepthAbove = 0;
          let waterHeight = Number.MIN_SAFE_INTEGER;
          let stoneDepthOffset = Number.MAX_SAFE_INTEGER;
          
          for (let y = chunk.maxY; y >= chunk.minY; y -= 1) {
              const worldPos = BlockPos.create(worldX, y, worldZ);
              const oldState = chunk.getBlockState(worldPos);
              if (oldState.equals(BlockState.AIR)) {
                  stoneDepthAbove = 0;
                  waterHeight = Number.MIN_SAFE_INTEGER;
                  continue;
              }
              if (oldState.isFluid()) {
                  if (waterHeight === Number.MIN_SAFE_INTEGER) {
                      waterHeight = y + 1;
                  }
                  continue;
              }
              if (stoneDepthOffset >= y) {
                  stoneDepthOffset = Number.MIN_SAFE_INTEGER;
                  for (let i = y - 1; i >= chunk.minY; i -= 1) {
                      const state = chunk.getBlockState(BlockPos.create(worldX, i, worldZ));
                      if (state.equals(BlockState.AIR) || state.isFluid()) {
                          stoneDepthOffset = i + 1;
                          break;
                      }
                  }
              }
              stoneDepthAbove += 1;
              const stoneDepthBelow = y - stoneDepthOffset + 1;
              if (!oldState.equals((this as any).defaultBlock)) {
                  continue;
              }
              surfaceContext.updateY(stoneDepthAbove, stoneDepthBelow, waterHeight, y);
              const newState = ruleWithContext(worldX, y, worldZ);
              if (newState) {
                  chunk.setBlockState(worldPos, newState);
              }
          }
      }
  }
}
