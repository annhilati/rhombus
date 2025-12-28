from rhombus.language import *
from rhombus.core.df_types import MIN_REASONABLE_VALUE, MAX_REASONABLE_VALUE

def overworld():
    cave_layer = NoiseReference("minecraft:cave_layer")
    cave_cheese = NoiseReference("minecraft:cave_cheese")

    cave_pillars = range_choice(
        input="minecraft:overworld/caves/pillars",
        max_exclusive=0.03,
        min_inclusive=MIN_REASONABLE_VALUE,
        when_in_range=MIN_REASONABLE_VALUE,
        when_out_of_range="minecraft:overworld/caves/pillars"
    )

    caves = max(
        min(
            min(
                add(
                    4 * noise(cave_layer, xz_scale=1, y_scale=8) ** 2,
                    clamp(0.27 + noise(cave_cheese, xz_scale=1, y_scale=2/3),
                        min=-1,
                        max=1
                    ) + clamp(
                        1.5 + (-0.64 * DensityReference("minecraft:overworld/sloped_cheese")),
                        min=0,
                        max=0.5
                    )
                    
                ),
                "minecraft:overworld/caves/entrances"
            ),
            DensityReference("minecraft:overworld/caves/spaghetti_2d") + DensityReference("minecraft:overworld/caves/spaghetti_roughness_function")
        ),
        cave_pillars
    )

    terrain_vs_cave_selector = range_choice(
        input="minecraft:overworld/sloped_cheese",
        max_exclusive=1.5625,
        min_inclusive=MIN_REASONABLE_VALUE,
        when_in_range=min("minecraft:overworld/sloped_cheese", 5 * DensityReference("minecraft:overworld/caves/entrances")),
        when_out_of_range=caves
    )

    return min(
        squeeze(
            0.64 * interpolated(
                blend_density(
                    0.1171875 + (
                        y_clamped_gradient(-64, -40, 0, 1)
                        * (-0.1171875 + -0.078125 + (y_clamped_gradient(240, 256, 1, 0) * (0.078125 + terrain_vs_cave_selector)))
                    )
                )
            )
        ),
        "minecraft:overworld/caves/noodle"
    )

print(overworld())
print(overworld().as_dict())