
from typing import Literal
from Rhombus.core.params import SubParameters
from Rhombus.core.density_function import DensityFunction
from Rhombus.core.utils import JSONDict
from Rhombus.language import DensityDescriptor, BuiltinWizard
from dataclasses import dataclass

@dataclass
class RandomSampler(SubParameters):
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
    
    def encode(self) -> JSONDict:
        return {**{
            parameter: (
                ... if False
                    
                else value)
            for parameter, value
            in self.fields.items()
            if value is not None and parameter != "Lambda"
        },
        **({"lambda": self.Lambda} if self.Lambda is not None else {})
        }


@dataclass
class DistanceMetric(SubParameters):
    type: Literal["chebyshev", "euclidean", "manhattan", "minkowski"]

    # minowski
    p: int              = None

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
    count: int  # >= 0
    lacunarity: float
    persistence: float


@dataclass
class DerivativeComponent(SubParameters):
    step: int       # > 0
    direction: DensityFunction

    @BuiltinWizard
    def __init__(self, step: int, direction: DensityDescriptor):
        self.step = step
        self.direction = direction