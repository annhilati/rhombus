from rhombus import *
from rhombus.std.types_legacy.vanilla_legacy import weird_scaled_sampler

register(support.vanilla_legacy.weird_scaled_sampler)

noise_jagged = Noise(
    -16,
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
)
noise_offset = Noise(-3, [1.0, 1.0, 1.0, 0.0])
noise_erosion = Noise(-9, [1.0, 1.0, 0.0, 1.0, 1.0])
noise_continentalness = Noise(-9, [1.0, 1.0, 2.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0])
noise_ridge = Noise(-7, [1.0, 2.0, 1.0, 0.0, 0.0, 0.0])
noise_cave_layer = Noise(-8, [1.0])

shift_z = flat_cache(cache_2d(shift_b(argument=noise_offset)))
shift_x = flat_cache(cache_2d(shift_a(argument=noise_offset)))
y = coords.y()

overworld_erosion = flat_cache(
    shifted_noise(
        noise=noise_erosion,
        shift_x=shift_x,
        shift_y=0.0,
        shift_z=shift_z,
        xz_scale=0.25,
        y_scale=0.0,
    )
)
overworld_continents = flat_cache(
    shifted_noise(
        noise=noise_continentalness,
        shift_x=shift_x,
        shift_y=0.0,
        shift_z=shift_z,
        xz_scale=0.25,
        y_scale=0.0,
    )
)
overworld_ridges = flat_cache(
    shifted_noise(
        noise=noise_ridge,
        shift_x=shift_x,
        shift_y=0.0,
        shift_z=shift_z,
        xz_scale=0.25,
        y_scale=0.0,
    )
)
overworld_ridges_folded = -3.0 * (-1 / 3 + abs((-2 / 3 + abs(overworld_ridges))))
overworld_offset = flat_cache(
    (
        cache_2d(
            (
                (blend_offset() * (1.0 + (-1.0 * cache_once(blend_alpha()))))
                + (
                    (
                        -0.5037500262260437
                        + spline(
                            coordinate=overworld_continents,
                            points=[
                                (-1.1, 0.044, 0.0),
                                (-1.02, -0.2222, 0.0),
                                (-0.51, -0.2222, 0.0),
                                (-0.44, -0.12, 0.0),
                                (-0.18, -0.12, 0.0),
                                (
                                    -0.16,
                                    spline(
                                        coordinate=overworld_erosion,
                                        points=[
                                            (
                                                -0.85,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.08880186, 0.38940096),
                                                        (1.0, 0.69000006, 0.38940096),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.7,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (
                                                            -1.0,
                                                            -0.115760356,
                                                            0.37788022,
                                                        ),
                                                        (1.0, 0.6400001, 0.37788022),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.4,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.2222, 0.0),
                                                        (-0.75, -0.2222, 0.0),
                                                        (-0.65, 0.0, 0.0),
                                                        (0.5954547, 2.9802322e-08, 0.0),
                                                        (
                                                            0.6054547,
                                                            2.9802322e-08,
                                                            0.2534563,
                                                        ),
                                                        (1.0, 0.100000024, 0.2534563),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.35,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.3, 0.5),
                                                        (-0.4, 0.05, 0.0),
                                                        (0.0, 0.05, 0.0),
                                                        (0.4, 0.05, 0.0),
                                                        (1.0, 0.060000002, 0.007000001),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.1,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.15, 0.5),
                                                        (-0.4, 0.0, 0.0),
                                                        (0.0, 0.0, 0.0),
                                                        (0.4, 0.05, 0.1),
                                                        (1.0, 0.060000002, 0.007000001),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.2,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.15, 0.5),
                                                        (-0.4, 0.0, 0.0),
                                                        (0.0, 0.0, 0.0),
                                                        (0.4, 0.0, 0.0),
                                                        (1.0, 0.0, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.7,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.02, 0.0),
                                                        (-0.4, -0.03, 0.0),
                                                        (0.0, -0.03, 0.0),
                                                        (0.4, 0.0, 0.06),
                                                        (1.0, 0.0, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                        ],
                                    ),
                                    0.0,
                                ),
                                (
                                    -0.15,
                                    spline(
                                        coordinate=overworld_erosion,
                                        points=[
                                            (
                                                -0.85,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.08880186, 0.38940096),
                                                        (1.0, 0.69000006, 0.38940096),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.7,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (
                                                            -1.0,
                                                            -0.115760356,
                                                            0.37788022,
                                                        ),
                                                        (1.0, 0.6400001, 0.37788022),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.4,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.2222, 0.0),
                                                        (-0.75, -0.2222, 0.0),
                                                        (-0.65, 0.0, 0.0),
                                                        (0.5954547, 2.9802322e-08, 0.0),
                                                        (
                                                            0.6054547,
                                                            2.9802322e-08,
                                                            0.2534563,
                                                        ),
                                                        (1.0, 0.100000024, 0.2534563),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.35,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.3, 0.5),
                                                        (-0.4, 0.05, 0.0),
                                                        (0.0, 0.05, 0.0),
                                                        (0.4, 0.05, 0.0),
                                                        (1.0, 0.060000002, 0.007000001),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.1,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.15, 0.5),
                                                        (-0.4, 0.0, 0.0),
                                                        (0.0, 0.0, 0.0),
                                                        (0.4, 0.05, 0.1),
                                                        (1.0, 0.060000002, 0.007000001),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.2,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.15, 0.5),
                                                        (-0.4, 0.0, 0.0),
                                                        (0.0, 0.0, 0.0),
                                                        (0.4, 0.0, 0.0),
                                                        (1.0, 0.0, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.7,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.02, 0.0),
                                                        (-0.4, -0.03, 0.0),
                                                        (0.0, -0.03, 0.0),
                                                        (0.4, 0.0, 0.06),
                                                        (1.0, 0.0, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                        ],
                                    ),
                                    0.0,
                                ),
                                (
                                    -0.1,
                                    spline(
                                        coordinate=overworld_erosion,
                                        points=[
                                            (
                                                -0.85,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.08880186, 0.38940096),
                                                        (1.0, 0.69000006, 0.38940096),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.7,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (
                                                            -1.0,
                                                            -0.115760356,
                                                            0.37788022,
                                                        ),
                                                        (1.0, 0.6400001, 0.37788022),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.4,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.2222, 0.0),
                                                        (-0.75, -0.2222, 0.0),
                                                        (-0.65, 0.0, 0.0),
                                                        (0.5954547, 2.9802322e-08, 0.0),
                                                        (
                                                            0.6054547,
                                                            2.9802322e-08,
                                                            0.2534563,
                                                        ),
                                                        (1.0, 0.100000024, 0.2534563),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.35,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.25, 0.5),
                                                        (-0.4, 0.05, 0.0),
                                                        (0.0, 0.05, 0.0),
                                                        (0.4, 0.05, 0.0),
                                                        (1.0, 0.060000002, 0.007000001),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.1,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.1, 0.5),
                                                        (-0.4, 0.001, 0.01),
                                                        (0.0, 0.003, 0.01),
                                                        (0.4, 0.05, 0.094000004),
                                                        (1.0, 0.060000002, 0.007000001),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.2,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.1, 0.5),
                                                        (-0.4, 0.01, 0.0),
                                                        (0.0, 0.01, 0.0),
                                                        (0.4, 0.03, 0.04),
                                                        (1.0, 0.1, 0.049),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.7,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.02, 0.0),
                                                        (-0.4, -0.03, 0.0),
                                                        (0.0, -0.03, 0.0),
                                                        (0.4, 0.03, 0.12),
                                                        (1.0, 0.1, 0.049),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                        ],
                                    ),
                                    0.0,
                                ),
                                (
                                    0.25,
                                    spline(
                                        coordinate=overworld_erosion,
                                        points=[
                                            (
                                                -0.85,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, 0.20235021, 0.0),
                                                        (0.0, 0.7161751, 0.5138249),
                                                        (1.0, 1.23, 0.5138249),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.7,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, 0.2, 0.0),
                                                        (0.0, 0.44682026, 0.43317974),
                                                        (1.0, 0.88, 0.43317974),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.4,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, 0.2, 0.0),
                                                        (0.0, 0.30829495, 0.3917051),
                                                        (1.0, 0.70000005, 0.3917051),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.35,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.25, 0.5),
                                                        (-0.4, 0.35, 0.0),
                                                        (0.0, 0.35, 0.0),
                                                        (0.4, 0.35, 0.0),
                                                        (1.0, 0.42000002, 0.049000014),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.1,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.1, 0.5),
                                                        (-0.4, 0.0069999998, 0.07),
                                                        (0.0, 0.021, 0.07),
                                                        (0.4, 0.35, 0.658),
                                                        (1.0, 0.42000002, 0.049000014),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.2,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.1, 0.5),
                                                        (-0.4, 0.01, 0.0),
                                                        (0.0, 0.01, 0.0),
                                                        (0.4, 0.03, 0.04),
                                                        (1.0, 0.1, 0.049),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.4,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.1, 0.5),
                                                        (-0.4, 0.01, 0.0),
                                                        (0.0, 0.01, 0.0),
                                                        (0.4, 0.03, 0.04),
                                                        (1.0, 0.1, 0.049),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.45,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.1, 0.0),
                                                        (
                                                            -0.4,
                                                            spline(
                                                                coordinate=overworld_ridges_folded,
                                                                points=[
                                                                    (-1.0, -0.1, 0.5),
                                                                    (-0.4, 0.01, 0.0),
                                                                    (0.0, 0.01, 0.0),
                                                                    (0.4, 0.03, 0.04),
                                                                    (1.0, 0.1, 0.049),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                        (0.0, 0.17, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.55,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.1, 0.0),
                                                        (
                                                            -0.4,
                                                            spline(
                                                                coordinate=overworld_ridges_folded,
                                                                points=[
                                                                    (-1.0, -0.1, 0.5),
                                                                    (-0.4, 0.01, 0.0),
                                                                    (0.0, 0.01, 0.0),
                                                                    (0.4, 0.03, 0.04),
                                                                    (1.0, 0.1, 0.049),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                        (0.0, 0.17, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.58,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.1, 0.5),
                                                        (-0.4, 0.01, 0.0),
                                                        (0.0, 0.01, 0.0),
                                                        (0.4, 0.03, 0.04),
                                                        (1.0, 0.1, 0.049),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.7,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.02, 0.0),
                                                        (-0.4, -0.03, 0.0),
                                                        (0.0, -0.03, 0.0),
                                                        (0.4, 0.03, 0.12),
                                                        (1.0, 0.1, 0.049),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                        ],
                                    ),
                                    0.0,
                                ),
                                (
                                    1.0,
                                    spline(
                                        coordinate=overworld_erosion,
                                        points=[
                                            (
                                                -0.85,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, 0.34792626, 0.0),
                                                        (0.0, 0.9239631, 0.5760369),
                                                        (1.0, 1.5, 0.5760369),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.7,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, 0.2, 0.0),
                                                        (0.0, 0.5391705, 0.4608295),
                                                        (1.0, 1.0, 0.4608295),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.4,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, 0.2, 0.0),
                                                        (0.0, 0.5391705, 0.4608295),
                                                        (1.0, 1.0, 0.4608295),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.35,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.2, 0.5),
                                                        (-0.4, 0.5, 0.0),
                                                        (0.0, 0.5, 0.0),
                                                        (0.4, 0.5, 0.0),
                                                        (1.0, 0.6, 0.070000015),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.1,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.05, 0.5),
                                                        (-0.4, 0.01, 0.099999994),
                                                        (0.0, 0.03, 0.099999994),
                                                        (0.4, 0.5, 0.94),
                                                        (1.0, 0.6, 0.070000015),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.2,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.05, 0.5),
                                                        (-0.4, 0.01, 0.0),
                                                        (0.0, 0.01, 0.0),
                                                        (0.4, 0.03, 0.04),
                                                        (1.0, 0.1, 0.049),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.4,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.05, 0.5),
                                                        (-0.4, 0.01, 0.0),
                                                        (0.0, 0.01, 0.0),
                                                        (0.4, 0.03, 0.04),
                                                        (1.0, 0.1, 0.049),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.45,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.05, 0.0),
                                                        (
                                                            -0.4,
                                                            spline(
                                                                coordinate=overworld_ridges_folded,
                                                                points=[
                                                                    (-1.0, -0.05, 0.5),
                                                                    (-0.4, 0.01, 0.0),
                                                                    (0.0, 0.01, 0.0),
                                                                    (0.4, 0.03, 0.04),
                                                                    (1.0, 0.1, 0.049),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                        (0.0, 0.17, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.55,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.05, 0.0),
                                                        (
                                                            -0.4,
                                                            spline(
                                                                coordinate=overworld_ridges_folded,
                                                                points=[
                                                                    (-1.0, -0.05, 0.5),
                                                                    (-0.4, 0.01, 0.0),
                                                                    (0.0, 0.01, 0.0),
                                                                    (0.4, 0.03, 0.04),
                                                                    (1.0, 0.1, 0.049),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                        (0.0, 0.17, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.58,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.05, 0.5),
                                                        (-0.4, 0.01, 0.0),
                                                        (0.0, 0.01, 0.0),
                                                        (0.4, 0.03, 0.04),
                                                        (1.0, 0.1, 0.049),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.7,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-1.0, -0.02, 0.015),
                                                        (-0.4, 0.01, 0.0),
                                                        (0.0, 0.01, 0.0),
                                                        (0.4, 0.03, 0.04),
                                                        (1.0, 0.1, 0.049),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                        ],
                                    ),
                                    0.0,
                                ),
                            ],
                        )
                    )
                    * (cache_once(blend_alpha()))
                )
            )
        )
    )
)
overworld_depth = y_clamped_gradient(
    from_value=1.5, from_y=-64, to_value=-1.5, to_y=320
) + (overworld_offset)
overworld_jaggedness = flat_cache(
    cache_2d(
        (
            0.0
            + (
                blend_alpha()
                * (
                    -0.0
                    + spline(
                        coordinate=overworld_continents,
                        points=[
                            (-0.11, 0.0, 0.0),
                            (
                                0.03,
                                spline(
                                    coordinate=overworld_erosion,
                                    points=[
                                        (
                                            -1.0,
                                            spline(
                                                coordinate=overworld_ridges_folded,
                                                points=[
                                                    (0.19999999, 0.0, 0.0),
                                                    (0.44999996, 0.0, 0.0),
                                                    (
                                                        1.0,
                                                        spline(
                                                            coordinate=overworld_ridges,
                                                            points=[
                                                                (-0.01, 0.63, 0.0),
                                                                (0.01, 0.3, 0.0),
                                                            ],
                                                        ),
                                                        0.0,
                                                    ),
                                                ],
                                            ),
                                            0.0,
                                        ),
                                        (
                                            -0.78,
                                            spline(
                                                coordinate=overworld_ridges_folded,
                                                points=[
                                                    (0.19999999, 0.0, 0.0),
                                                    (0.44999996, 0.0, 0.0),
                                                    (
                                                        1.0,
                                                        spline(
                                                            coordinate=overworld_ridges,
                                                            points=[
                                                                (-0.01, 0.315, 0.0),
                                                                (0.01, 0.15, 0.0),
                                                            ],
                                                        ),
                                                        0.0,
                                                    ),
                                                ],
                                            ),
                                            0.0,
                                        ),
                                        (
                                            -0.5775,
                                            spline(
                                                coordinate=overworld_ridges_folded,
                                                points=[
                                                    (0.19999999, 0.0, 0.0),
                                                    (0.44999996, 0.0, 0.0),
                                                    (
                                                        1.0,
                                                        spline(
                                                            coordinate=overworld_ridges,
                                                            points=[
                                                                (-0.01, 0.315, 0.0),
                                                                (0.01, 0.15, 0.0),
                                                            ],
                                                        ),
                                                        0.0,
                                                    ),
                                                ],
                                            ),
                                            0.0,
                                        ),
                                        (-0.375, 0.0, 0.0),
                                    ],
                                ),
                                0.0,
                            ),
                            (
                                0.65,
                                spline(
                                    coordinate=overworld_erosion,
                                    points=[
                                        (
                                            -1.0,
                                            spline(
                                                coordinate=overworld_ridges_folded,
                                                points=[
                                                    (0.19999999, 0.0, 0.0),
                                                    (
                                                        0.44999996,
                                                        spline(
                                                            coordinate=overworld_ridges,
                                                            points=[
                                                                (-0.01, 0.63, 0.0),
                                                                (0.01, 0.3, 0.0),
                                                            ],
                                                        ),
                                                        0.0,
                                                    ),
                                                    (
                                                        1.0,
                                                        spline(
                                                            coordinate=overworld_ridges,
                                                            points=[
                                                                (-0.01, 0.63, 0.0),
                                                                (0.01, 0.3, 0.0),
                                                            ],
                                                        ),
                                                        0.0,
                                                    ),
                                                ],
                                            ),
                                            0.0,
                                        ),
                                        (
                                            -0.78,
                                            spline(
                                                coordinate=overworld_ridges_folded,
                                                points=[
                                                    (0.19999999, 0.0, 0.0),
                                                    (0.44999996, 0.0, 0.0),
                                                    (
                                                        1.0,
                                                        spline(
                                                            coordinate=overworld_ridges,
                                                            points=[
                                                                (-0.01, 0.63, 0.0),
                                                                (0.01, 0.3, 0.0),
                                                            ],
                                                        ),
                                                        0.0,
                                                    ),
                                                ],
                                            ),
                                            0.0,
                                        ),
                                        (
                                            -0.5775,
                                            spline(
                                                coordinate=overworld_ridges_folded,
                                                points=[
                                                    (0.19999999, 0.0, 0.0),
                                                    (0.44999996, 0.0, 0.0),
                                                    (
                                                        1.0,
                                                        spline(
                                                            coordinate=overworld_ridges,
                                                            points=[
                                                                (-0.01, 0.63, 0.0),
                                                                (0.01, 0.3, 0.0),
                                                            ],
                                                        ),
                                                        0.0,
                                                    ),
                                                ],
                                            ),
                                            0.0,
                                        ),
                                        (-0.375, 0.0, 0.0),
                                    ],
                                ),
                                0.0,
                            ),
                        ],
                    )
                )
            )
        )
    )
)
overworld_base_3d_noise = old_blended_noise(
    smear_scale_multiplier=8.0,
    xz_factor=80.0,
    xz_scale=0.25,
    y_factor=160.0,
    y_scale=0.125,
)
overworld_factor = flat_cache(
    (
        cache_2d(
            (
                10.0
                + (
                    blend_alpha()
                    * (
                        -10.0
                        + spline(
                            coordinate=overworld_continents,
                            points=[
                                (-0.19, 3.95, 0.0),
                                (
                                    -0.15,
                                    spline(
                                        coordinate=overworld_erosion,
                                        points=[
                                            (
                                                -0.6,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 6.25, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.5,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.05, 6.3, 0.0),
                                                        (0.05, 2.67, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.35,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 6.25, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.25,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 6.25, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.1,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.05, 2.67, 0.0),
                                                        (0.05, 6.3, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.03,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 6.25, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (0.35, 6.25, 0.0),
                                            (
                                                0.45,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-0.9, 6.25, 0.0),
                                                        (
                                                            -0.69,
                                                            spline(
                                                                coordinate=overworld_ridges,
                                                                points=[
                                                                    (0.0, 6.25, 0.0),
                                                                    (0.1, 0.625, 0.0),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.55,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-0.9, 6.25, 0.0),
                                                        (
                                                            -0.69,
                                                            spline(
                                                                coordinate=overworld_ridges,
                                                                points=[
                                                                    (0.0, 6.25, 0.0),
                                                                    (0.1, 0.625, 0.0),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (0.62, 6.25, 0.0),
                                        ],
                                    ),
                                    0.0,
                                ),
                                (
                                    -0.1,
                                    spline(
                                        coordinate=overworld_erosion,
                                        points=[
                                            (
                                                -0.6,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 5.47, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.5,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.05, 6.3, 0.0),
                                                        (0.05, 2.67, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.35,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 5.47, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.25,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 5.47, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.1,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.05, 2.67, 0.0),
                                                        (0.05, 6.3, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.03,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 5.47, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (0.35, 5.47, 0.0),
                                            (
                                                0.45,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-0.9, 5.47, 0.0),
                                                        (
                                                            -0.69,
                                                            spline(
                                                                coordinate=overworld_ridges,
                                                                points=[
                                                                    (0.0, 5.47, 0.0),
                                                                    (0.1, 0.625, 0.0),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.55,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-0.9, 5.47, 0.0),
                                                        (
                                                            -0.69,
                                                            spline(
                                                                coordinate=overworld_ridges,
                                                                points=[
                                                                    (0.0, 5.47, 0.0),
                                                                    (0.1, 0.625, 0.0),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (0.62, 5.47, 0.0),
                                        ],
                                    ),
                                    0.0,
                                ),
                                (
                                    0.03,
                                    spline(
                                        coordinate=overworld_erosion,
                                        points=[
                                            (
                                                -0.6,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 5.08, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.5,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.05, 6.3, 0.0),
                                                        (0.05, 2.67, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.35,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 5.08, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.25,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 5.08, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.1,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.05, 2.67, 0.0),
                                                        (0.05, 6.3, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.03,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 5.08, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (0.35, 5.08, 0.0),
                                            (
                                                0.45,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-0.9, 5.08, 0.0),
                                                        (
                                                            -0.69,
                                                            spline(
                                                                coordinate=overworld_ridges,
                                                                points=[
                                                                    (0.0, 5.08, 0.0),
                                                                    (0.1, 0.625, 0.0),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.55,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (-0.9, 5.08, 0.0),
                                                        (
                                                            -0.69,
                                                            spline(
                                                                coordinate=overworld_ridges,
                                                                points=[
                                                                    (0.0, 5.08, 0.0),
                                                                    (0.1, 0.625, 0.0),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (0.62, 5.08, 0.0),
                                        ],
                                    ),
                                    0.0,
                                ),
                                (
                                    0.06,
                                    spline(
                                        coordinate=overworld_erosion,
                                        points=[
                                            (
                                                -0.6,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 4.69, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.5,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.05, 6.3, 0.0),
                                                        (0.05, 2.67, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.35,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 4.69, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.25,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 4.69, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                -0.1,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.05, 2.67, 0.0),
                                                        (0.05, 6.3, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.03,
                                                spline(
                                                    coordinate=overworld_ridges,
                                                    points=[
                                                        (-0.2, 6.3, 0.0),
                                                        (0.2, 4.69, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.05,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (
                                                            0.45,
                                                            spline(
                                                                coordinate=overworld_ridges,
                                                                points=[
                                                                    (-0.2, 6.3, 0.0),
                                                                    (0.2, 4.69, 0.0),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                        (0.7, 1.56, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.4,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (
                                                            0.45,
                                                            spline(
                                                                coordinate=overworld_ridges,
                                                                points=[
                                                                    (-0.2, 6.3, 0.0),
                                                                    (0.2, 4.69, 0.0),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                        (0.7, 1.56, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.45,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (
                                                            -0.7,
                                                            spline(
                                                                coordinate=overworld_ridges,
                                                                points=[
                                                                    (-0.2, 6.3, 0.0),
                                                                    (0.2, 4.69, 0.0),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                        (-0.15, 1.37, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (
                                                0.55,
                                                spline(
                                                    coordinate=overworld_ridges_folded,
                                                    points=[
                                                        (
                                                            -0.7,
                                                            spline(
                                                                coordinate=overworld_ridges,
                                                                points=[
                                                                    (-0.2, 6.3, 0.0),
                                                                    (0.2, 4.69, 0.0),
                                                                ],
                                                            ),
                                                            0.0,
                                                        ),
                                                        (-0.15, 1.37, 0.0),
                                                    ],
                                                ),
                                                0.0,
                                            ),
                                            (0.58, 4.69, 0.0),
                                        ],
                                    ),
                                    0.0,
                                ),
                            ],
                        )
                    )
                )
            )
        )
    )
)


overworld_sloped_cheese = (
    4.0
    * quarter_negative(
        (
            (
                overworld_depth
                + (
                    overworld_jaggedness
                    * half_negative(
                        noise(noise=noise_jagged, xz_scale=1500.0, y_scale=0.0)
                    )
                )
            )
            * overworld_factor
        )
    )
    + overworld_base_3d_noise
)

overworld_caves_pillars = cache_once(
    (
        (
            (2.0 * noise(noise=Noise(-7, [1.0, 1.0]), xz_scale=25.0, y_scale=0.3))
            + (-1.0 + (-1.0 * noise(noise=Noise(-8, [1.0]), xz_scale=1.0, y_scale=1.0)))
        )
        * cube(
            (0.55 + (0.55 * noise(noise=Noise(-8, [1.0]), xz_scale=1.0, y_scale=1.0)))
        )
    )
)
overworld_caves_noodles = range_choice(
    input=interpolated(
        range_choice(
            input=y,
            max_exclusive=321.0,
            min_inclusive=-60.0,
            when_in_range=noise(noise=Noise(-8, [1.0]), xz_scale=1.0, y_scale=1.0),
            when_out_of_range=-1.0,
        )
    ),
    max_exclusive=0.0,
    min_inclusive=-1000000.0,
    when_in_range=64.0,
    when_out_of_range=(
        interpolated(
            range_choice(
                input=y,
                max_exclusive=321.0,
                min_inclusive=-60.0,
                when_in_range=(
                    -0.07500000000000001
                    + (
                        -0.025
                        * noise(noise=Noise(-8, [1.0]), xz_scale=1.0, y_scale=1.0)
                    )
                ),
                when_out_of_range=0.0,
            )
        )
        + (
            1.5
            * max(
                abs(
                    interpolated(
                        range_choice(
                            input=y,
                            max_exclusive=321.0,
                            min_inclusive=-60.0,
                            when_in_range=noise(
                                noise=Noise(-7, [1.0]),
                                xz_scale=2.6666666666666665,
                                y_scale=2.6666666666666665,
                            ),
                            when_out_of_range=0.0,
                        )
                    )
                ),
                abs(
                    interpolated(
                        range_choice(
                            input=y,
                            max_exclusive=321.0,
                            min_inclusive=-60.0,
                            when_in_range=noise(
                                noise=Noise(-7, [1.0]),
                                xz_scale=2.6666666666666665,
                                y_scale=2.6666666666666665,
                            ),
                            when_out_of_range=0.0,
                        )
                    )
                ),
            )
        )
    ),
)
overworld_caves_spaghetti_roughness_function = cache_once(
    (
        (-0.05 + (-0.05 * noise(noise=Noise(-8, [1.0]), xz_scale=1.0, y_scale=1.0)))
        * (-0.4 + abs(noise(noise=Noise(-5, [1.0]), xz_scale=1.0, y_scale=1.0)))
    )
)
overworld_caves_entrances = cache_once(
    min(
        (
            (0.37 + noise(noise=Noise(-7, [0.4, 0.5, 1.0]), xz_scale=0.75, y_scale=0.5))
            + y_clamped_gradient(from_value=0.3, from_y=-10, to_value=0.0, to_y=30)
        ),
        (
            overworld_caves_spaghetti_roughness_function
            + clamp(
                input=(
                    max(
                        weird_scaled_sampler(
                            input=cache_once(
                                noise(
                                    noise=Noise(-11, [1.0]), xz_scale=2.0, y_scale=1.0
                                )
                            ),
                            noise=Noise(-7, [1.0]),
                            rarity_value_mapper="type_1",
                        ),
                        weird_scaled_sampler(
                            input=cache_once(
                                noise(
                                    noise=Noise(-11, [1.0]), xz_scale=2.0, y_scale=1.0
                                )
                            ),
                            noise=Noise(-7, [1.0]),
                            rarity_value_mapper="type_1",
                        ),
                    )
                    + (
                        -0.0765
                        + (
                            -0.011499999999999996
                            * noise(noise=Noise(-8, [1.0]), xz_scale=1.0, y_scale=1.0)
                        )
                    )
                ),
                max=1.0,
                min=-1.0,
            )
        ),
    )
)
overworld_caves_spaghetti_2d_thickness_modulator = cache_once(
    (-0.95 + (-0.35 * noise(noise=Noise(-11, [1.0]), xz_scale=2.0, y_scale=1.0)))
)
overworld_caves_spaghetti_2d = clamp(
    input=max(
        (
            weird_scaled_sampler(
                input=noise(noise=Noise(-11, [1.0]), xz_scale=2.0, y_scale=1.0),
                noise=Noise(-7, [1.0]),
                rarity_value_mapper="type_2",
            )
            + (0.083 * overworld_caves_spaghetti_2d_thickness_modulator)
        ),
        cube(
            (
                abs(
                    (
                        (
                            0.0
                            + (
                                8.0
                                * noise(
                                    noise=Noise(-8, [1.0]), xz_scale=1.0, y_scale=0.0
                                )
                            )
                        )
                        + y_clamped_gradient(
                            from_value=8.0, from_y=-64, to_value=-40.0, to_y=320
                        )
                    )
                )
                + overworld_caves_spaghetti_2d_thickness_modulator
            )
        ),
    ),
    max=1.0,
    min=-1.0,
)

final_destiny = min(
    squeeze(
        (
            0.64
            * interpolated(
                blend_density(
                    (
                        0.1171875
                        + (
                            y_clamped_gradient(
                                from_value=0.0, from_y=-64, to_value=1.0, to_y=-40
                            )
                            * (
                                -0.1171875
                                + (
                                    -0.078125
                                    + (
                                        y_clamped_gradient(
                                            from_value=1.0,
                                            from_y=240,
                                            to_value=0.0,
                                            to_y=256,
                                        )
                                        * (
                                            0.078125
                                            + range_choice(
                                                input=overworld_sloped_cheese,
                                                max_exclusive=1.5625,
                                                min_inclusive=-1000000.0,
                                                when_in_range=min(
                                                    overworld_sloped_cheese,
                                                    (5.0 * overworld_caves_entrances),
                                                ),
                                                when_out_of_range=max(
                                                    min(
                                                        min(
                                                            (
                                                                (
                                                                    4.0
                                                                    * square(
                                                                        noise(
                                                                            noise=noise_cave_layer,
                                                                            xz_scale=1.0,
                                                                            y_scale=8.0,
                                                                        )
                                                                    )
                                                                )
                                                                + (
                                                                    clamp(
                                                                        input=(
                                                                            0.27
                                                                            + noise(
                                                                                noise="minecraft:cave_cheese",
                                                                                xz_scale=1.0,
                                                                                y_scale=0.6666666666666666,
                                                                            )
                                                                        ),
                                                                        max=1.0,
                                                                        min=-1.0,
                                                                    )
                                                                    + clamp(
                                                                        input=(
                                                                            1.5
                                                                            + (
                                                                                -0.64
                                                                                * overworld_sloped_cheese
                                                                            )
                                                                        ),
                                                                        max=0.5,
                                                                        min=0.0,
                                                                    )
                                                                )
                                                            ),
                                                            overworld_caves_entrances,
                                                        ),
                                                        (
                                                            overworld_caves_spaghetti_2d
                                                            + overworld_caves_spaghetti_roughness_function
                                                        ),
                                                    ),
                                                    range_choice(
                                                        input=overworld_caves_pillars,
                                                        max_exclusive=0.03,
                                                        min_inclusive=-1000000.0,
                                                        when_in_range=-1000000.0,
                                                        when_out_of_range=overworld_caves_pillars,
                                                    ),
                                                ),
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    ),
    overworld_caves_noodles,
)
