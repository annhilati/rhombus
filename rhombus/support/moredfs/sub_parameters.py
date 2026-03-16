
from typing import Literal
from dataclasses import dataclass
from rhombus.core import (
    SubParameters,
    DensityFunction,
    JSONDict,
    annotated_fields,
    fEncode,
    fDecode
)
from rhombus.language.density import DensityDescriptor, BuiltinWizard

@dataclass
class RandomSampler(SubParameters):
    """Describes a sampler for random values.

    **NOTE** Use these factories for instanciating:
    - `.Beta()` 
    - `.Binomial()` 
    - `.Exponential()` 
    - `.Gamma()` 
    - `.Geometric()` 
    - `.Normal()` 
    - `.Poisson()` 
    - `.Uniform()` 
    
    [More Density Functions Wiki Reference](https://github.com/klinbee/More-Density-Functions/wiki#random-sampler-types)
    """
    type: Literal["beta", "binomial", "exponential", "gamma", "geometric", "normal", "poisson", "uniform"]

    # beta
    alpha: float        = None # > 0
    beta: float         = None # > 0
    # binomial
    trials: int         = None # 0 < x < 1000000
    # binomial / geometric
    probability: float  = None # 0 =< x =< 1
    # exponential / poisson
    Lambda: float       = None # > 0
    # gamma
    shape: float        = None # > 0
    scale: float        = None
    # normal
    mean: float         = None
    std_dev: float      = None # > 0
    # uniform
    min: float          = None
    max: float          = None # >= min

    @classmethod
    def Beta(cls, alpha: float, beta: float):
        return cls(type="beta", alpha=alpha, beta=beta)
    @classmethod
    def Binomial(cls, trials: int, probability: float):
        return cls(type="binomial", trials=trials, probability=probability)
    @classmethod
    def Exponential(cls, Lambda: float):
        return cls(type="exponential", Lambda=Lambda)
    @classmethod
    def Gamma(cls, shape: float, scale: float):
        return cls(type="gamma", shape=shape, scale=scale)
    @classmethod
    def Geometric(cls, probability):
        return cls(type="geometric", probability=probability)
    @classmethod
    def Normal(cls, mean: float, std_dev: float):
        return cls(type="normal", mean=mean, std_dev=std_dev)
    @classmethod
    def Poisson(cls, Lambda: float):
        return cls(type="poisson", Lambda=Lambda)
    @classmethod
    def Uniform(cls, min: float, max: float):
        return cls(type="uniform", min=min, max=max)
    
    @classmethod
    def decode(cls, data: JSONDict) -> "RandomSampler":
        fields = annotated_fields(cls)

        return cls(**{
            parameter: fDecode(value, tp)
            for parameter, value in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
            if parameter != "lambda"
        },
        **({"lambda": data["lambda"]} if data.get("lambda", None) is not None else {}))
    
    def encode(self) -> JSONDict:
        return {**{
            parameter: fEncode(value)
            for parameter, value
            in self.fields.items()
            if value is not None and parameter != "Lambda"
        },
        **({"lambda": self.Lambda} if self.Lambda is not None else {})
        }
    


@dataclass
class DistanceMetric(SubParameters):
    """Describes a procedure to determine distances between n-dimensional points.

    **NOTE** Use these factories for instanciating:
    - `.Chebyshev()` 
    - `.Euclidean()` 
    - `.Manhattan()` 
    - `.Minowski()` 
    
    [More Density Functions Wiki Reference](https://github.com/klinbee/More-Density-Functions/wiki#distance-metric-types)
    """
    type: Literal["chebyshev", "euclidean", "manhattan", "minkowski"]

    # minowski
    p: int = None

    @classmethod
    def Chebyshev(cls) -> "DistanceMetric":
        return cls("chebyshev")
    @classmethod
    def Euclidean(cls) -> "DistanceMetric":
        return cls("euclidean")
    @classmethod
    def Manhattan(cls) -> "DistanceMetric":
        return cls("manhattan")
    @classmethod
    def Minowski(cls, p: int) -> "DistanceMetric":
        return cls("minkowski", p=p)


@dataclass
class ExtraOctaves(SubParameters):
    """
    [More Density Functions Wiki Reference](https://github.com/klinbee/More-Density-Functions/wiki#value-noise)
    """
    count: int  # >= 0
    lacunarity: float
    persistence: float


@dataclass
class DerivativeComponent(SubParameters):
    """
    [More Density Functions Wiki Reference](https://github.com/klinbee/More-Density-Functions/wiki#derivative)
    """
    step: int       # > 0
    direction: DensityFunction

    @BuiltinWizard
    def __init__(self, step: int, direction: DensityDescriptor):
        self.step = step
        self.direction = direction