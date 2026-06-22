import { DensityFunction } from 'deepslate'

const originalAp2Compute = DensityFunction.Ap2.prototype.compute

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
