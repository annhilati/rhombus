from typing import ClassVar, Self, Literal, Optional
from rhombus.core.density_function import DensityFunction, MappedFunctionBase, SimpleFunctionBase, DoubleArgumentFunctionBase
from .sub_parameters import DistanceMetric, RandomSampler, ExtraOctaves, DerivativeComponent

#======// Density Function Base Classes //=======================================================//

class DivisionFunctionBase(DensityFunction):
    numerator: DensityFunction
    denominator: DensityFunction

    @classmethod
    def deserialize(cls, data: dict) -> Self:
        numerator = data["argument1"]
        denominator = data["argument2"]
        return cls(
            DensityFunction.deserialize_inline(numerator),
            DensityFunction.deserialize_inline(denominator),
        )
    
    def serialize(self) -> dict:
        return {"type": self.id, "numerator": self.numerator.serialize_inline(), "denominator": self.denominator.serialize_inline()}
    

#======// Function Type Classes //===============================================================//

class acos(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:acos"
    
class asin(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:asin"

class atan(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:atan"

class cbrt(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:cbrt"

class ceil(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:ceil"

class clamp(DensityFunction):
    id: ClassVar[str] = "moredfs:clamp"
    input: DensityFunction
    min: float
    max:float

class cos(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:cos"

class cosh(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:cosh"

class derivative():
    id: ClassVar[str] = "moredfs:derivative"
    argument: DensityFunction
    component_x: Optional[DerivativeComponent] = None
    component_y: Optional[DerivativeComponent] = None
    component_z: Optional[DerivativeComponent] = None
    # One of the components must be defined at least

class distance(DensityFunction):
    id: ClassVar[str] = "moredfs:distance"
    distance_metric: DistanceMetric
    point1: Optional[list[DensityFunction]] = None
    point2: Optional[list[DensityFunction]] = None

class div(DivisionFunctionBase):
    id: ClassVar[str] = "moredfs:div"

class dot_product(DensityFunction):
    id: ClassVar[str] = "moredfs:dot_product"
    argument1: DensityFunction
    argument2: DensityFunction
    step_x: int = None
    step_y: int = None
    step_z: int = None

class floor(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:floor"

class floor_div(DivisionFunctionBase):
    id: ClassVar[str] = "moredfs:floor_div"

class floor_mod(DivisionFunctionBase):
    id: ClassVar[str] = "moredfs:floor_mod"

class gapped_grid_square_spiral():
    id: ClassVar[str] = "moredfs:gapped_grid_square_spiral"
    x_size: int # > 0
    z_size: int # > 0
    spacing: int # > 0
    grid_cell_args: list[DensityFunction]
    out_of_bounds_argument: DensityFunction

class gradient_magnitude(DensityFunction):
    id: ClassVar[str] = "mroedfs:gradient_magnitude"
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

class log2(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:log2"

class log2_floor(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:log2_floor"

class mod(DivisionFunctionBase):
    id: ClassVar[str] = "moredfs:mod"

class ln(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:ln"

class negate(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:negate"

class or_else(DensityFunction):
    id: ClassVar[str] = "moredfs:or_else"
    argument: DensityFunction
    fallback: DensityFunction

class polar_coords(SimpleFunctionBase):
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

class radius(SimpleFunctionBase):
    id: ClassVar[str] = "moredfs:radius"

class radius_3d(SimpleFunctionBase):
    id: ClassVar[str] = "moredfs:radius_3d"

class reciprocal(DensityFunction):
    id: ClassVar[str] = "moredfs:reciprocal"
    denominator: DensityFunction

class remainder(DivisionFunctionBase):
    id: ClassVar[str] = "moredfs:remainder"

class resolver(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:resolver"

class round(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:round"

class shift():
    id: ClassVar[str] = "moredfs:shift"
    argument: DensityFunction
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction

class sigmoid(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:sigmoid"

class signum(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:signum"

class sin(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:sin"

class sinh(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:sinh"

class single_channel_image_tessellation(DensityFunction):
    id: ClassVar[str] = "moredfs:single_channel_image_tessellation"
    x_size: int
    z_size: int
    deflated_frame_data: str

class sqrt(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:sqrt"

class subtract(DoubleArgumentFunctionBase):
    id: ClassVar[str] = "moredfs:subtract"

class tan(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:tan"

class tanh(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:tanh"

class value_noise(DensityFunction):
    id: ClassVar[str] = "moredfs:value_noise"
    sampler: RandomSampler
    size_x: int # >= 0
    size_y: int # >= 0
    size_z: int # >= 0
    interpolation: Literal["none", "lerp", "smoothstep"]
    salt: Optional[int] = None
    extra_octaves: Optional[ExtraOctaves] = None

class vector_angle(DoubleArgumentFunctionBase):
    id: ClassVar[str] = "moredfs:vector_angle"

class x(SimpleFunctionBase):
    id: ClassVar[str] = "moredfs:x"

class x_clamped_gradient(DensityFunction):
    id: ClassVar[str] = "moredfs:x_clamped_gradient"
    from_x: int
    to_x: int
    from_value: float
    to_value: float

class y(SimpleFunctionBase):
    id: ClassVar[str] = "moredfs:y"

class z(SimpleFunctionBase):
    id: ClassVar[str] = "moredfs:z"

class z_clamped_gradient(DensityFunction):
    id: ClassVar[str] = "moredfs:z_clamped_gradient"
    from_z: int
    to_z: int
    from_value: float
    to_value: float