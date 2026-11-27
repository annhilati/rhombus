from typing import Literal
from rhombus import *

n = Noise(-8, [1])

base = noise(n, y_scale = 0)

delta = math.linalg.DensityVector(
    3 * (noise(n, shift_x=30, y_scale=0) - base),
    3 * (noise(n, shift_z=30, y_scale=0) - base)
)
twist = math.linalg.DensityMatrix(
    (0.5, -base),
    (base, 0.5)
)
twisted = twist @ delta

main = math.smax(0.1, noise(n, shift_x=350 * twisted[0], shift_z=350 * twisted[1], y_scale=0))

##############################

@macro
def cellular_noise_v1(d: int = 32):

    # center coords of the blocks original grid cell
    current_grid_center = math.linalg.DensityVector(
        x() // d + d/2,
        y() // d + d/2,
        z() // d + d/2
    ).element_transform(lambda df: Density.partitioned(df))

    distances: list[Density] = []
    values: list[Density] = []
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for k in (-1, 0, 1):

                grid_center = current_grid_center + math.linalg.DensityVector(i, j, k) * d

                feature_point_jitter = math.linalg.DensityVector(
                    noises.random(-1/3 * d, 1/3 * d, key="fpjx"),
                    noises.random(-1/3 * d, 1/3 * d, key="fpjy"),
                    noises.random(-1/3 * d, 1/3 * d, key="fpjz")
                ).element_transform(lambda df: coords.domain_pin(cache(df), x=grid_center[0], y=grid_center[1], z=grid_center[2])).element_transform(lambda df: Density.partitioned(df))

                feature_point = grid_center + feature_point_jitter

                dvec = feature_point - math.linalg.DensityVector(x(), y(), z())

                distance = Density.partitioned(math.linalg.norm(dvec))
                
                distances.append(distance)
                values.append(feature_point_jitter[0]) # test-wise


    min_distance = min(*distances).named("min")

    cond = conditional.when(1).equals(0).then(0) # remove this somehow
    for i, distance in enumerate(distances):
        cond.elsewhen(distance).equals(min_distance).then(values[i])
    
    return cond.otherwise(0)


@macro
def cellular_noise_optimized(
    d: int = 32,
    *,
    dim: Literal[2, 3] = 2,
    return_type: Literal["distance", "value"] = "distance",
    jitter: float = 0.9,
    upscale_cell_size: int = 1,
    seed_key: str = "opt_cell",
) -> Density:
    """Optimized vanilla cellular (Voronoi / Worley) noise for Rhombus.

    Features:
    - dim=2 (default, 9 neighbor cells for terrain/biomes) or dim=3 (27 cells).
    - Squared-distance comparisons (avoids expensive sqrt calls in distance minimization).
    - Uncorrelated, amplified jitter per axis breaking square grid alignment without crossing cell bounds.
    - return_type="distance" (Worley F1 distance, zero conditionals!) or "value" (flat Voronoi cell plateaus).
    - Automatic partitioning of cell origins and minimum distance.
    - Optional upscale_cell_size (> 1 uses minecraft:upscale for fast preview sampling).
    """
    max_jitter = (d / 2) * min(jitter, 0.9)

    jx_noise = Noise(0, [1], base_amplitude=1).named(f"rhombus:noise/{seed_key}_jx")
    jz_noise = Noise(0, [1], base_amplitude=1).named(f"rhombus:noise/{seed_key}_jz")
    jy_noise = Noise(0, [1], base_amplitude=1).named(f"rhombus:noise/{seed_key}_jy") if dim == 3 else None
    val_noise = Noise(0, [1], base_amplitude=1).named(f"rhombus:noise/{seed_key}_val") if return_type == "value" else None

    def get_jitter(n, cx, cy, cz):
        raw = coords.domain_pin(cache(noise(n)), x=cx, y=cy, z=cz)
        return clamp(raw * 2.5, -1.0, 1.0) * max_jitter

    if dim == 2:
        # Pre-partition cell origins
        base_x = Density.partitioned((x() // d) * d)
        base_z = Density.partitioned((z() // d) * d)

        distances_sq: list[Density] = []
        cell_values: list[Density] = []

        offsets = (
            (-1, -1), (-1, 0), (-1, 1),
            ( 0, -1), ( 0, 0), ( 0, 1),
            ( 1, -1), ( 1, 0), ( 1, 1),
        )

        for i, k in offsets:
            center_x = base_x + (i * d + d / 2)
            center_z = base_z + (k * d + d / 2)

            jx = get_jitter(jx_noise, center_x, 0, center_z)
            jz = get_jitter(jz_noise, center_x, 0, center_z)

            fp_x = center_x + jx
            fp_z = center_z + jz

            dx = fp_x - x()
            dz = fp_z - z()

            # Squared Euclidean distance avoids sqrt in min()
            dist_sq = Density.partitioned(dx * dx + dz * dz)
            distances_sq.append(dist_sq)

            if return_type == "value":
                val = coords.domain_pin(cache(noise(val_noise)), x=center_x, y=0, z=center_z)
                cell_values.append(Density.partitioned(val))

        min_dist_sq = Density.partitioned(min(*distances_sq))

        if return_type == "distance":
            # Normalized Worley distance (0 at center, ~1 at borders)
            res = sqrt(min_dist_sq) / (d / 2)
        else:
            cond = conditional.when(1).equals(0).then(0)
            for dist_sq, val in zip(distances_sq, cell_values):
                cond.elsewhen(dist_sq).equals(min_dist_sq).then(val)
            res = cond.otherwise(0)

    else:  # dim == 3
        base_x = Density.partitioned((x() // d) * d)
        base_y = Density.partitioned((y() // d) * d)
        base_z = Density.partitioned((z() // d) * d)

        distances_sq = []
        cell_values = []

        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for k in (-1, 0, 1):
                    center_x = base_x + (i * d + d / 2)
                    center_y = base_y + (j * d + d / 2)
                    center_z = base_z + (k * d + d / 2)

                    jx = get_jitter(jx_noise, center_x, center_y, center_z)
                    jy = get_jitter(jy_noise, center_x, center_y, center_z)
                    jz = get_jitter(jz_noise, center_x, center_y, center_z)

                    dx = (center_x + jx) - x()
                    dy = (center_y + jy) - y()
                    dz = (center_z + jz) - z()

                    dist_sq = Density.partitioned(dx * dx + dy * dy + dz * dz)
                    distances_sq.append(dist_sq)

                    if return_type == "value":
                        val = coords.domain_pin(cache(noise(val_noise)), x=center_x, y=center_y, z=center_z)
                        cell_values.append(Density.partitioned(val))

        min_dist_sq = Density.partitioned(min(*distances_sq))
        if return_type == "distance":
            res = sqrt(min_dist_sq) / (d / 2)
        else:
            cond = conditional.when(1).equals(0).then(0)
            for dist_sq, val in zip(distances_sq, cell_values):
                cond.elsewhen(dist_sq).equals(min_dist_sq).then(val)
            res = cond.otherwise(0)

    if upscale_cell_size > 1:
        res = upscale(
            res,
            x_cell_size=upscale_cell_size,
            z_cell_size=upscale_cell_size,
            y_cell_size=upscale_cell_size if dim == 3 else 1,
            x_mode="nearest_neighbor",
            z_mode="nearest_neighbor",
            y_mode="nearest_neighbor",
        )

    return res



# preview.serve(("main", Noise(-8,[1,1,1,1,1,1,1,1,1,1,1,1,1,1])()))
preview.serve(("main", cellular_noise_optimized(dim=2, return_type="value")))