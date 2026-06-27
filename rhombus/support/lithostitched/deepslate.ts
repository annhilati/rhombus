interface Window {
    rhombus: {
        deepslate: any;
        densityFunctions: Map<string, (obj: any, inputParser: any) => any>;
        visualizers: Map<string, any>;
        React: any;
    };
}

const { deepslate, densityFunctions } = window.rhombus;

class LithostitchedSqrt extends deepslate.DensityFunction {
    input: any;

    constructor(input: any) {
        super();
        this.input = input;
    }

    compute(context: any): number {
        return Math.sqrt(Math.max(0, this.input.compute(context)));
    }

    maxValue(): number {
        return Math.sqrt(Math.max(0, this.input.maxValue()));
    }

    minValue(): number {
        // Da Math.sqrt monoton steigend ist, ist das Minimum = sqrt(minValue) (oder 0, falls negativ)
        return Math.sqrt(Math.max(0, this.input.minValue()));
    }

    mapAll(visitor: any): any {
        return visitor.map(new LithostitchedSqrt(this.input.mapAll(visitor)));
    }
}

densityFunctions.set('lithostitched:sqrt', (obj: any, inputParser: any) => {
    return new LithostitchedSqrt(inputParser(obj.argument));
});
