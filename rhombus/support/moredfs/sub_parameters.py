from typing import Literal

from rhombus.core import (
    SubParameters,
    DensityFunction,
    field
)
from rhombus.std.density import Density, AnyDensity


class RandomSampler(SubParameters):
    """Describes a sampler for random values.

    **NOTE:** Use these factories for instanciating:
    - `~.Beta()`
    - `~.Binomial()`
    - `~.Exponential()`
    - `~.Gamma()`
    - `~.Geometric()`
    - `~.Normal()`
    - `~.Poisson()`
    - `~.Uniform()`

    [More Density Functions Wiki Reference](https://github.com/klinbee/More-Density-Functions/wiki#random-sampler-types)
    """

    type: Literal[
        "beta",
        "binomial",
        "exponential",
        "gamma",
        "geometric",
        "normal",
        "poisson",
        "uniform",
    ] = field(legacy_values={
        "2.1.2": {
            "beta": "moredfs:beta",
            "binomial": "moredfs:binomial",
            "exponential": "moredfs:exponential",
            "gamma": "moredfs:gamma",
            "geometric": "moredfs:geometric",
            "normal": "moredfs:normal",
            "poisson": "moredfs:poisson",
            "uniform": "moredfs:uniform",
        }
    })

    # beta
    alpha: float = field(None, validate=lambda x: x > 0)
    beta: float = field(None, validate=lambda x: x > 0)
    # binomial
    trials: int = field(None, validate=lambda x: 0 < x < 1000000) # Check whether < or <=
    # binomial / geometric
    probability: float = field(None, validate=lambda x: 0 <= x <= 1)
    # exponential / poisson
    Lambda: float = field(None, legacy_keys={1000000: "lambda"}, validate=lambda x: x > 0)
    # gamma
    shape: float = field(None, validate=lambda x: x > 0)
    scale: float = None
    # normal
    mean: float = None
    std_dev: float = field(None, validate=lambda x: x > 0)
    # uniform
    min: float = None
    max: float = field(None, validate=lambda x, s: x > s.min)

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


class DistanceMetric(SubParameters):
    """Describes a procedure to determine distances between n-dimensional points.

    **NOTE:** Use these factories for instanciating:
    - `~.Chebyshev()`
    - `~.Euclidean()`
    - `~.Manhattan()`
    - `~.Minowski()`

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


class ExtraOctaves(SubParameters):
    """
    [More Density Functions Wiki Reference](https://github.com/klinbee/More-Density-Functions/wiki#value-noise)
    """

    count: int = field(validate=lambda x: x >= 0)
    lacunarity: float
    persistence: float


class DerivativeComponent(SubParameters):
    """
    [More Density Functions Wiki Reference](https://github.com/klinbee/More-Density-Functions/wiki#derivative)
    """

    step: int = field(validate=lambda x: x > 0)
    direction: DensityFunction

    def __init__(self, step: int, direction: AnyDensity):
        self.step = step
        self.direction = Density(direction).AST


class JitterSampler(SubParameters):
    """Sampler for adding positional jitter, e.g. in voronoi cells."""
    x: RandomSampler
    y: RandomSampler
    z: RandomSampler
