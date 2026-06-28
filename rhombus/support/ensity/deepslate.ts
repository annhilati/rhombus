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

//======// En-sityFunctions //=============================================================//

class EnsityLonelyIsland extends deepslate.DensityFunction {
    constructor() { super(); }
    compute(context: any): number {
        const x = Math.floor(context.x / 8);
        const z = Math.floor(context.z / 8);
        const h = Math.sqrt(x * x + z * z) * 8.0;
        const val = Math.max(-100.0, Math.min(80.0, 100.0 - h));
        return (val - 8.0) / 128.0;
    }
    minValue(): number { return -0.84375; }
    maxValue(): number { return 0.5625; }
    mapAll(visitor: any): any { return visitor.map(this); }
}

densityFunctions.set('msg:lonely_island', () => new EnsityLonelyIsland());

class EnsityFloatingIslands extends deepslate.DensityFunction {
    islandNoise: any;
    
    constructor(seed: bigint) {
        super();
        const randomSource = new deepslate.LegacyRandom(seed);
        if (typeof randomSource.consumeCount === 'function') {
            randomSource.consumeCount(17292);
        } else if (typeof randomSource.consume === 'function') {
            randomSource.consume(17292);
        } else if (typeof randomSource.advance === 'function') {
            randomSource.advance(17292);
        } else {
            for (let i = 0; i < 17292; i++) randomSource.nextInt();
        }
        this.islandNoise = new deepslate.SimplexNoise(randomSource);
    }
    
    getHeightValue(x: number, z: number): number {
        let i = Math.floor(x / 2); x = x % 2;
        let j = Math.floor(z / 2); z = z % 2;
        let f = -100.0;
        
        for (let m = -12; m <= 12; ++m) {
            for (let n = -12; n <= 12; ++n) {
                let o = i + m;
                let p = j + n;
                // sample2D handles the (double x, double y) mapping of java's SimplexNoise.getValue
                if (this.islandNoise.sample2D(o, p) < -0.8999999761581421) {
                    let g = (Math.abs(o) * 3439.0 + Math.abs(p) * 147.0) % 13.0 + 9.0;
                    let h = x - m * 2;
                    let q = z - n * 2;
                    let r = 100.0 - Math.sqrt(h * h + q * q) * g;
                    r = Math.max(-100.0, Math.min(80.0, r));
                    f = Math.max(f, r);
                }
            }
        }
        return f;
    }
    
    compute(context: any): number {
        return (this.getHeightValue(Math.floor(context.x / 8), Math.floor(context.z / 8)) - 8.0) / 128.0;
    }
    
    minValue(): number { return -0.84375; }
    maxValue(): number { return 0.5625; }
    mapAll(visitor: any): any { return visitor.map(this); }
}

densityFunctions.set('msg:floating_islands', () => new EnsityFloatingIslands(0n));
