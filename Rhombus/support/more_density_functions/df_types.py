from typing import ClassVar, Self
from dataclasses import dataclass
from Rhombus.core.density_function import DensityFunction, MappedFunctionBase, SimpleFunctionBase, DoubleArgumentFunctionBase, MultiArgumentsFunctionBase, decode_HOLDER_HELPER_CODEC

TODO = "TODO"

#======// Function Type Base Classes //==========================================================//

@dataclass
class DivisionFunctionBase(DensityFunction):
    numerator: DensityFunction
    denominator: DensityFunction

    @classmethod
    def decode(cls, data: dict) -> Self:
        numerator = data["argument1"]
        denominator = data["argument2"]
        return cls(
            decode_HOLDER_HELPER_CODEC(numerator),
            decode_HOLDER_HELPER_CODEC(denominator)
        )
    
    def encode(self) -> dict:
        return {"type": self.id, "numerator": self.numerator.encode(), "denominator": self.denominator.encode()}
    

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

@dataclass
class clamp(MultiArgumentsFunctionBase):
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
    TODO

class distance():
    id: ClassVar[str] = "moredfs:distance"
    TODO

class div(DivisionFunctionBase):
    id: ClassVar[str] = "moredfs:div"

@dataclass
class dot_product(MultiArgumentsFunctionBase):
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
    TODO
    # Here are lists of DFTypes

@dataclass
class gradient_magnitude(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "mroedfs:gradient_magnitude"
    argument: DensityFunction
    step_x: int = None
    step_y: int = None
    step_z: int = None

class ieee_rem(DivisionFunctionBase):
    id: ClassVar[str] = "moredfs:ieee_rem"

class log():
    id: ClassVar[str] = "moredfs:log"
    TODO

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

@dataclass
class or_else(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "moredfs:or_else"
    argument: DensityFunction
    fallback: DensityFunction

class polar_coords(SimpleFunctionBase):
    id: ClassVar[str] = "moredfs:polar_coords"

class power():
    id: ClassVar[str] = "moredfs:power"
    TODO

@dataclass
class profiler(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "moredfs:profiler"
    argument: DensityFunction
    warm_up: int
    iterations: int

class radius(SimpleFunctionBase):
    id: ClassVar[str] = "moredfs:radius"

class radius_3d(SimpleFunctionBase):
    id: ClassVar[str] = "moredfs:radius_3d"

@dataclass
class reciprocal(MultiArgumentsFunctionBase):
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
    TODO

class sigmoid(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:sigmoid"

class signum(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:signum"

class sin(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:sin"

class sinh(MappedFunctionBase):
    id: ClassVar[str] = "moredfs:sinh"

@dataclass
class single_channel_image_tessellation(MultiArgumentsFunctionBase):
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

class value_noise():
    id: ClassVar[str] = "moredfs:value_noise"
    TODO

class vector_angle(DoubleArgumentFunctionBase):
    id: ClassVar[str] = "moredfs:vector_angle"

class x(SimpleFunctionBase):
    id: ClassVar[str] = "moredfs:x"

dataclass
class x_clamped_gradient(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "moredfs:x_clamped_gradient"
    from_x: int
    to_x: int
    from_value: float
    to_value: float

class y(SimpleFunctionBase):
    id: ClassVar[str] = "moredfs:y"

class z(SimpleFunctionBase):
    id: ClassVar[str] = "moredfs:z"

@dataclass
class z_clamped_gradient(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "moredfs:z_clamped_gradient"
    from_z: int
    to_z: int
    from_value: float
    to_value: float