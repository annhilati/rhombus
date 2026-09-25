export {};

declare global {
    interface Window {
        rhombus: {
            deepslate: any;
            densityFunctions: Map<string, (obj: any, inputParser: any) => any>;
            visualizers: Map<string, any>;
            React: any;
            FastNoiseLite: any;
            pako: any;
        };
    }
}

const { deepslate, densityFunctions } = window.rhombus;

//======// Tectonic //=============================================================//

class TectonicConfigClamp extends deepslate.DensityFunction {
    input: any; min: any; max: any;
    constructor(input: any, min: any, max: any) {
        super(); this.input = input; this.min = min; this.max = max;
    }
    compute(context: any): number {
        return Math.min(Math.max(this.input.compute(context), this.min.compute(context)), this.max.compute(context));
    }
    range(): any { return deepslate.Interval.of(this.getMin(), this.getMax()); }
    getMin(): number { return ((this.min.range && typeof this.min.range === 'function') ? this.min.range() : deepslate.Interval.ofExact(0)).min; }
    getMax(): number { return ((this.max.range && typeof this.max.range === 'function') ? this.max.range() : deepslate.Interval.ofExact(0)).max; }
    mapChildren(visitor: any): any { return new TectonicConfigClamp(visitor.apply(this.input), visitor.apply(this.min), visitor.apply(this.max)); }
}
densityFunctions.set('tectonic:config_clamp', (obj: any, parser: any) => new TectonicConfigClamp(parser(obj.input), parser(obj.min), parser(obj.max)));

class TectonicInvert extends deepslate.DensityFunction {
    input: any; minVal: number; maxVal: number;
    constructor(input: any, minVal: number, maxVal: number) {
        super(); this.input = input; this.minVal = minVal; this.maxVal = maxVal;
    }
    compute(context: any): number {
        return 1.0 / this.input.compute(context);
    }
    range(): any { return deepslate.Interval.of(this.getMin(), this.getMax()); }
    getMin(): number { return this.minVal; }
    getMax(): number { return this.maxVal; }
    mapChildren(visitor: any): any { return new TectonicInvert(visitor.apply(this.input), this.minVal, this.maxVal); }
}
densityFunctions.set('tectonic:invert', (obj: any, parser: any) => {
    // In Java, min/max bounds are precomputed based on the input's min/max.
    // If the input spans across 0, bounds are -Infinity to Infinity.
    const parsedInput = parser(obj.argument);
    const min = ((parsedInput.range && typeof parsedInput.range === 'function') ? parsedInput.range() : deepslate.Interval.ofExact(0)).min;
    const max = ((parsedInput.range && typeof parsedInput.range === 'function') ? parsedInput.range() : deepslate.Interval.ofExact(0)).max;
    let invertMin = min;
    let invertMax = max;
    if (min < 0 && max > 0) {
        invertMin = -Infinity;
        invertMax = Infinity;
    }
    return new TectonicInvert(parsedInput, invertMin, invertMax);
});

// Explicit errors for unmockable config dependencies
densityFunctions.set('tectonic:config_constant', () => {
    throw new Error('tectonic:config_constant is not supported in Rhombus Preview yet');
});

densityFunctions.set('tectonic:config_noise', () => {
    throw new Error('tectonic:config_noise is not supported in Rhombus Preview yet');
});
