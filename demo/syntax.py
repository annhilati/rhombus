from Rhombus import *

distance_scale = ConfiguredDensity("config:distance_scale", default=1.0)

def radius() -> Density:
    x = coords.x()
    z = coords.z()

    return math.sqrt(abs(x)**2 + abs(z)**2, iterations=1)


n = Noise(-6, [1, 0.5, 0.25, 0.125])

hopper = radius() * distance_scale + y_clamped_gradient(from_y=0, to_y=100, from_value=-100, to_value=100)

out = hopper | noise(n, xz_scale=1, y_scale=1)
# Cut the shape of the sampled noise from the hopper

print(out)