from density.functions import *
from density import Density, Noise, NoiseReference, functions

def overworld():
    cave_layer = NoiseReference("minecraft:cave_layer")
    cave_cheese = NoiseReference("minecraft:cave_cheese")

    cave_pillars = range_choice(
        "minecraft:overworld/caves/pillars",
        0.03,
        -1000000.0,
        -1000000.0,
        "minecraft:overworld/caves/pillars"
    )

    caves = max(
        min(
            min(
                add(
                    4 * noise(cave_layer, xz_scale=1, y_scale=8) ** 2,
                    clamp(0.27 + noise(cave_cheese, xz_scale=1, y_scale=0.6666666666666666),
                        -1,
                        1
                    ) + clamp(
                        1.5 + mul(-0.64, "minecraft:overworld/sloped_cheese"),
                        0,
                        0.5
                    )
                    
                ),
                "minecraft:overworld/caves/entrances"
            ),
            add("minecraft:overworld/caves/spaghetti_2d", "minecraft:overworld/caves/spaghetti_roughness_function")
        ),
        cave_pillars
    )

    terrain_vs_cave_selector = range_choice(
        input="minecraft:overworld/sloped_cheese",
        max_exclusive=1.5625,
        min_inclusive=-1000000.0,
        when_in_range=min("minecraft:overworld/sloped_cheese", mul(5, "minecraft:overworld/caves/entrances")),
        when_out_of_range=caves
    )

    return min(
        squeeze(
            mul(
                0.64,
                interpolated(
                    blend_density(
                        add(
                            0.1171875,
                            mul(
                                y_clamped_gradient(
                                    -64, 
                                    -40,
                                    0,
                                    1
                                ),
                                -0.1171875 + -0.078125 + (y_clamped_gradient(240, 256, 1, 0) * (0.078125 + terrain_vs_cave_selector))

                            )
                        )
                    )
                )
            )
        ),
        "minecraft:overworld/caves/noodle"
    )

print(overworld())
print(overworld().as_json())