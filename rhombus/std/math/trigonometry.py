import math as py_math

from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro
from rhombus.std.math import _splinelib, splines, e, NaN
from rhombus.std import caching, conditional

from rhombus.core.environment import env

pi = 3.1415926535897932 # 38462643383279502884197169399375105820974944592307816406
"The constant `π` to 16 decimals."


# ======// Sinic Approximations //===============================================================//

@macro
def sin(df: AnyDensity) -> Density:
    return splines.spline(df % (2 * pi), _splinelib.sample_spline_points(py_math.sin, (-pi, pi), 5))

@macro
def cos(df: AnyDensity) -> Density:
    return splines.spline(df % (2 * pi), _splinelib.sample_spline_points(py_math.cos, (-pi, pi), 5))

# ======// Derived Trigonometric Functions //====================================================//

@macro
def tan(df: AnyDensity) -> Density:
    return caching.specified_cache(sin(df) / cos(df), df)

@macro
def cot(df: AnyDensity) -> Density:
    return caching.specified_cache(cos(df) / sin(df), df)

@macro
def sec(df: AnyDensity) -> Density:
    return 1 / cos(df)

@macro
def csc(df: AnyDensity) -> Density:
    return 1 / sin(df)

# ======// Inverse Trigonometric Functions //====================================================//

@macro
def asin(df: AnyDensity) -> Density:
    return (
        conditional.when(df)
        .inside(-1, 1)
        .then(caching.specified_cache(atan(df / (1 - df**2)**0.5), df))
        .otherwise(NaN)
    )

@macro
def acos(df: AnyDensity) -> Density:
    return pi/2 - asin(df)

@macro
def atan(df: AnyDensity) -> Density:
    return splines.spline(df, _splinelib.sample_spline_points(py_math.atan, (-8, 8), points=5))

@macro
def acot(df: AnyDensity) -> Density:
    return atan(1/df)

@macro
def asec(df: AnyDensity) -> Density:
    return (
        conditional.when(df)
        .atmost(-1)
        .then(pi - atan((df**2 - 1)**0.5))
        .elsewhen(df)
        .atleast(1)
        .then(atan((df**2 - 1)**0.5))
        .otherwise(NaN)
    )

@macro
def acsc(df: AnyDensity) -> Density:
    return (
        conditional.when(df)
        .atmost(-1)
        .then(- atan(1 / (df**2 - 1)**0.5))
        .elsewhen(df)
        .atleast(1)
        .then(atan(1 / (df**2 - 1)**0.5))
        .otherwise(NaN)
    )


# ======// Hyperbolic Trigonometric Functions //=================================================//

@macro
def sinh(df: AnyDensity) -> Density:
    return (e**df - e**(-df)) / 2

@macro
def cosh(df: AnyDensity) -> Density:
    return (e**df + e**(-df)) / 2

@macro
def tanh(df: AnyDensity) -> Density:
    if env.datapack_version < 113:
        return splines.spline(df, _splinelib.sample_spline_points(py_math.tanh, (-3.5, 3.5), points=5))
    return (e**df - e**(-df)) / (e**df + e**(-df))

@macro
def coth(df: AnyDensity) -> Density:
    if env.datapack_version < 113:
        return 1 / tanh(df)
    return (e**df + e**(-df)) / (e**df - e**(-df))

@macro
def sech(df: AnyDensity) -> Density:
    return 2 / (e**df + e**(-df))

@macro
def csch(df: AnyDensity) -> Density:
    return 2 / (e**df - e**(-df))
