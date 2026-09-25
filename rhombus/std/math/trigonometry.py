import math as py_math

from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro, implementation
from rhombus.std.math.general import spline
from rhombus.std.math import _splinelib
from rhombus.std import caching, math


pi = 3.1415926535897932 # 38462643383279502884197169399375105820974944592307816406
"The constant `π` to 16 decimals."


# ======// Sinic Approximations //===============================================================//

@macro
def sin(df: AnyDensity) -> Density:
    return spline(df % (2 * pi), _splinelib.sample_spline_points(py_math.sin, (0, 2 * pi), 5))

@macro
def cos(df: AnyDensity) -> Density:
    return spline(df % (2 * pi), _splinelib.sample_spline_points(py_math.cos, (0, 2 * pi), 5))

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
    if -1 <= df <= 1:
        return caching.specified_cache(atan(df / (1 - df**2)**0.5), df)
    else:
        return math.NaN

@macro
def acos(df: AnyDensity) -> Density:
    return pi/2 - asin(df)

@macro
def atan(df: AnyDensity) -> Density:
    return spline(df, _splinelib.sample_spline_points(py_math.atan, (-8, 8), points=7))

@macro
def acot(df: AnyDensity) -> Density:
    return atan(1/df)

@macro
def asec(df: AnyDensity) -> Density:
    if df <= -1:
        return pi - atan((df**2 - 1)**0.5)
    elif df >= 1:
        return atan((df**2 - 1)**0.5)
    else:
        return math.NaN

@macro
def acsc(df: AnyDensity) -> Density:
    if df <= -1:
        return - atan(1 / (df**2 - 1)**0.5)
    elif df >= 1:
        return atan(1 / (df**2 - 1)**0.5)
    else:
        return math.NaN


# ======// Hyperbolic Trigonometric Functions //=================================================//

@macro
def sinh(df: AnyDensity) -> Density:
    @implementation(since=113)
    def sinh():
        return (math.e**df - math.e**(-df)) / 2

@macro
def cosh(df: AnyDensity) -> Density:
    @implementation(since=113)
    def cosh():
        return (math.e**df + math.e**(-df)) / 2

@macro
def tanh(df: AnyDensity) -> Density:
    @implementation(until=113)
    def tanh():
        return spline(df, _splinelib.sample_spline_points(py_math.tanh, (-3.5, 3.5), points=5))
    @implementation
    def tanh():
        return (math.e**df - math.e**(-df)) / (math.e**df + math.e**(-df))

@macro
def coth(df: AnyDensity) -> Density:
    @implementation(until=113)
    def coth():
        return 1 / tanh(df)
    @implementation
    def coth():
        return (math.e**df + math.e**(-df)) / (math.e**df - math.e**(-df))

@macro
def sech(df: AnyDensity) -> Density:
    @implementation(since=113)
    def sech():
        return 2 / (math.e**df + math.e**(-df))

@macro
def csch(df: AnyDensity) -> Density:
    @implementation(since=113)
    def csch():
        return 2 / (math.e**df - math.e**(-df))

# ======// Inverse Hyperbolic Trigonometric Functions //=========================================//

@macro
def arcsinh(df: AnyDensity) -> Density:
    @implementation(until=113)
    def arcsinh():
        spline(df, _splinelib.sample_spline_points(py_math.asinh, (-60, 60), points=14))
    @implementation
    def arcsinh():
        return math.log(df + math.sqrt(df**2 + 1))
    
# Check whether there are legacy implementations

@macro
def arccosh(df: AnyDensity) -> Density:
    @implementation(since=113)
    def arccosh():
        if df >= 1:
            return math.log(df + math.sqrt(df**2 - 1))
        else:
            return math.NaN
        
@macro
def arctanh(df: AnyDensity) -> Density:
    @implementation(since=113)
    def arctanh():
        if -1 < df < 1:
            return 0.5 * math.log((1+df) / (1-df))
        else:
            return math.NaN
        
@macro
def arccoth(df: AnyDensity) -> Density:
    @implementation(since=113)
    def arccoth():
        if df < -1 or df > 1:
            return 0.5 * math.log((1+df) / (1-df))
        else:
            return math.NaN
        
@macro
def arcsech(df: AnyDensity) -> Density:
    @implementation(since=113)
    def arcsech():
        if 0 < df <= 1:
            return math.log(1/df + math.sqrt(1/df**2 - 1))
        else:
            return math.NaN
        
@macro
def arccsch(df: AnyDensity) -> Density:
    @implementation(since=113)
    def arccsch():
        if df != 0:
            return math.log(1/df + math.sqrt(1/df**2 + 1))
        else:
            return math.NaN
        

# ======// arctan2 //============================================================================//

@macro
def arctan2(df1: AnyDensity, df2: AnyDensity) -> Density:
    # Returns pi for x < 0 and y == 0
    # https://en.wikipedia.org/wiki/Atan2
    # We do not use half-angle formula to avoid precission loss with the atan definition
    if df1 > 0:
        return atan(df2/df1)
    elif df1 < 0:
        if df2 > 0:
            return atan(df2/df1) + pi
        elif df2 == 0:
            return pi
        else:
            return atan(df2/df1) - pi
    else:
        if df2 > 0:
            return pi/2
        else:
            return - pi/2