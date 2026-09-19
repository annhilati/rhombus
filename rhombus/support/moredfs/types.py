from typing import ClassVar, Self, Literal, Optional

from rhombus.core import (
    DensityFunction,
    MappedDensityFunction,
    SimpleDensityFunction,
    DoubleArgumentDensityFunction,
    field
)

from .sub_parameters import (
    DistanceMetric,
    RandomSampler,
    ExtraOctaves,
    DerivativeComponent,
    JitterSampler,
)

# ======// Density Function Base Classes //=======================================================//


class DivisionFunctionBase(DensityFunction):
    numerator: DensityFunction
    denominator: DensityFunction


# ======// Function Type Classes //===============================================================//


class acos(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:acos"


class asin(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:asin"


class atan(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:atan"


class cache(MappedDensityFunction, versions=(..., "2.2.0")):
    id: ClassVar[str] = "moredfs:cache"


class cbrt(MappedDensityFunction, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:cbrt"


class ceil(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:ceil"


class clamp(DensityFunction):
    id: ClassVar[str] = "moredfs:clamp"
    input: DensityFunction
    min: float
    max: float


class cos(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:cos"


class cosh(MappedDensityFunction, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:cosh"


class derivative:
    id: ClassVar[str] = "moredfs:derivative"
    argument: DensityFunction
    component_x: Optional[DerivativeComponent] = field(None, validate=lambda x, df: len([v for v in [df.component_x, df.component_y, df.component_z] if v is None]) < 3)
    component_y: Optional[DerivativeComponent] = field(None, validate=lambda x, df: len([v for v in [df.component_x, df.component_y, df.component_z] if v is None]) < 3)
    component_z: Optional[DerivativeComponent] = field(None, validate=lambda x, df: len([v for v in [df.component_x, df.component_y, df.component_z] if v is None]) < 3)


class distance(DensityFunction, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:distance"
    distance_metric: DistanceMetric
    point1: Optional[list[DensityFunction]] = None
    point2: Optional[list[DensityFunction]] = None


class div(DivisionFunctionBase):
    id: ClassVar[str] = "moredfs:div"


class dot_product(DensityFunction, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:dot_product"
    argument1: DensityFunction
    argument2: DensityFunction
    step_x: int = None
    step_y: int = None
    step_z: int = None


class floor(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:floor"


class floor_div(DivisionFunctionBase):
    id: ClassVar[str] = "moredfs:floor_div"


class floor_mod(DivisionFunctionBase):
    id: ClassVar[str] = "moredfs:floor_mod"


class gapped_grid_square_spiral(DensityFunction, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:gapped_grid_square_spiral"
    x_size: int = field(validate=lambda x: x > 0)
    z_size: int = field(validate=lambda x: x > 0)
    spacing: int = field(validate=lambda x: x > 0)
    grid_cell_args: list[DensityFunction]
    out_of_bounds_argument: DensityFunction


class gradient_magnitude(DensityFunction):
    id: ClassVar[str] = "moredfs:gradient_magnitude"
    argument: DensityFunction
    step_x: int = None
    step_y: int = None
    step_z: int = None


class ieee_rem(DivisionFunctionBase):
    id: ClassVar[str] = "moredfs:ieee_rem"


class log(DensityFunction):
    id: ClassVar[str] = "moredfs:log"
    argument: DensityFunction
    base: DensityFunction


class log2(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:log2"


class log2_floor(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:log2_floor"


class mod(DivisionFunctionBase, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:mod"


class ln(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:ln"


class negate(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:negate"


class or_else(DensityFunction, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:or_else"
    argument: DensityFunction
    fallback: DensityFunction


class polar_coords(SimpleDensityFunction):
    id: ClassVar[str] = "moredfs:polar_coords"


class power(DensityFunction):
    id: ClassVar[str] = "moredfs:power"
    base: DensityFunction
    exponent: DensityFunction


class profiler(DensityFunction):
    id: ClassVar[str] = "moredfs:profiler"
    argument: DensityFunction
    warm_up: int
    iterations: int


class radius(SimpleDensityFunction, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:radius"


class radius_3d(SimpleDensityFunction, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:radius_3d"


class reciprocal(DensityFunction):
    id: ClassVar[str] = "moredfs:reciprocal"
    denominator: DensityFunction


class remainder(DivisionFunctionBase):
    id: ClassVar[str] = "moredfs:remainder"


class resolver(MappedDensityFunction, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:resolver"


class round(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:round"


class shift:
    id: ClassVar[str] = "moredfs:shift"
    argument: DensityFunction
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction


class sigmoid(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:sigmoid"


class signum(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:signum"


class sin(MappedDensityFunction):
    id: ClassVar[str] = field("moredfs:sin", legacy_values={"2.1.2": "moredfs:sine"})


class sinh(MappedDensityFunction, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:sinh"


class single_channel_image_tessellation(DensityFunction, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:single_channel_image_tessellation"
    x_size: int
    z_size: int
    deflated_frame_data: str


class sqrt(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:sqrt"


class subtract(DoubleArgumentDensityFunction):
    id: ClassVar[str] = "moredfs:subtract"


class tan(MappedDensityFunction):
    id: ClassVar[str] = "moredfs:tan"


class tanh(MappedDensityFunction, versions=("2.2.0", ...)):
    id: ClassVar[str] = "moredfs:tanh"


class value_noise(DensityFunction):
    id: ClassVar[str] = "moredfs:value_noise"
    sampler: RandomSampler
    size_x: int = field(validate=lambda x: x >= 0)
    size_y: int = field(validate=lambda x: x >= 0)
    size_z: int = field(validate=lambda x: x >= 0)
    interpolation: Literal["none", "lerp", "smoothstep"]
    salt: Optional[int] = None
    extra_octaves: Optional[ExtraOctaves] = None


class vector_angle(DoubleArgumentDensityFunction):
    id: ClassVar[str] = "moredfs:vector_angle"


class x(SimpleDensityFunction):
    id: ClassVar[str] = "moredfs:x"


class x_clamped_gradient(DensityFunction):
    id: ClassVar[str] = "moredfs:x_clamped_gradient"
    from_x: int
    to_x: int
    from_value: float
    to_value: float


class y(SimpleDensityFunction):
    id: ClassVar[str] = "moredfs:y"


class z(SimpleDensityFunction):
    id: ClassVar[str] = "moredfs:z"


class z_clamped_gradient(DensityFunction):
    id: ClassVar[str] = "moredfs:z_clamped_gradient"
    from_z: int
    to_z: int
    from_value: float
    to_value: float


class voronoi_cells(DensityFunction):
    id: ClassVar[str] = "moredfs:voronoi_cells"
    
    value_sampler: RandomSampler
    size_x: int
    size_y: int
    size_z: int
    jitter_sampler: JitterSampler
    distance_metric: DistanceMetric
    distance_type: Literal["f1", "f2", "f3"]
    exact: bool
    extra_octaves: ExtraOctaves
    salt: int


class worley_noise(DensityFunction):
    id: ClassVar[str] = "moredfs:worley_noise"
    
    size_x: int
    size_y: int
    size_z: int
    jitter_sampler: JitterSampler
    distance_metric: DistanceMetric
    distance_type: Literal["f1", "f2", "f3"]
    exact: bool
    invertValue: bool
    extra_octaves: ExtraOctaves
    salt: int
