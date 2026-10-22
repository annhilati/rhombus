from typing import ClassVar

from rhombus.core.models.density_function import (
    DensityFunction,
    field
)


class voronoi(DensityFunction):
    id: ClassVar[str] = "ikblibrary:voronoi"
    scale: float = field(validate=lambda x: x > 0)
    salt: int = 0
    flat: bool = True
    jitter: float = field(0.4, validate=lambda x: 0 <= x <= 0.5)
    metric: int = field(1, validate=lambda x: 0 <= x <= 5)
    mode: int = field(0, lambda x: 0 <= x <= 6)
    ordinal: int = field(1, validate=lambda x: 1 <= x <= 9)
    
    
class cached_voronoi(DensityFunction):
    id: ClassVar[str] = "ikblibrary:cached_voronoi"
    scale: float = field(validate=lambda x: x > 0)
    salt: int = 0
    flat: bool = True
    jitter: float = field(0.4, validate=lambda x: 0 <= x <= 0.5)
    metric: int = field(1, validate=lambda x: 0 <= x <= 5)
    maxCheck: int = field(3, validate=lambda x: 1 <= x <= 9)
    
    
class pull_cached_voronoi(DensityFunction):
    id: ClassVar[str] = "ikblibrary:pull_cached_voronoi"
    cache: DensityFunction # cached_voronoi
    ordinal: int = field(1, validate=lambda x: 1 <= x <= 9)
    mode: int = field(0, lambda x: 0 <= x <= 6)
    
    
class voronoi_dist(DensityFunction):
    id: ClassVar[str] = "ikblibrary:voronoi_dist"
    scale: float = field(validate=lambda x: x > 0)
    salt: int = 0
    flat: bool = True
    jitter: float = field(0.4, validate=lambda x: 0 <= x <= 0.5)
    metric: int = field(1, validate=lambda x: 0 <= x <= 5)
    ordinal: int = field(1, validate=lambda x: 1 <= x <= 9)
    rel: bool = False
    
    
class voronoi_center(DensityFunction):
    id: ClassVar[str] = "ikblibrary:voronoi_center"
    sampler: DensityFunction
    scale: float = field(validate=lambda x: x > 0)
    salt: int = 0
    flat: bool = True
    jitter: float = field(0.4, validate=lambda x: 0 <= x <= 0.5)
    metric: int = field(1, validate=lambda x: 0 <= x <= 5)
    ordinal: int = field(1, validate=lambda x: 1 <= x <= 9)
    
    
class sample_voronoi_center(DensityFunction):
    id: ClassVar[str] = "ikblibrary:sample_voronoi_center"
    cache: DensityFunction # cached_voronoi
    sampler: DensityFunction    
    ordinal: int = field(1, validate=lambda x: 1 <= x <= 9)


class near_sea(DensityFunction):
    id: ClassVar[str] = "ikblibrary:near_sea"
    cache: DensityFunction # cached_voronoi
    peak: float = field(0.25, validate=lambda x: 0 <= x <= 4)
    cont_bias: float = field(0.5, validate=lambda x: 0 <= x <= 1)
    distance: bool = True