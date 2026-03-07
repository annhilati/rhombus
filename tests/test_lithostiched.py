from Rhombus.support.lithostiched import FastNoiseConfig, fast_noise

c = FastNoiseConfig.SimplexNoise(frequency=1.0, fractal_type='ridged')

print(c.encode())

print(FastNoiseConfig.decode({'type': 'lithostiched:simplex', 'frequency': 1.0, 'fractal_type': 'ridged'}))