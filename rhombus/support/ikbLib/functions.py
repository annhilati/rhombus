import dataclasses

from rhombus.std.builtin import Density, AnyDensity, macro

from .types import voronoi as _voronoi, cached_voronoi, near_sea, pull_cached_voronoi, sample_voronoi_center, voronoi_center, voronoi_dist


@dataclasses.dataclass
class VoronoiNoise:
    scale: float
    jitter: float = 0.4
    metric: int = 1 # make this Literal
    flat: bool = True
    salt: int = 0


# TODO