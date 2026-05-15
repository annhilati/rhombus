from typing import overload, Literal, Callable
from rhombus.language import Density, DensityDescriptor, resolve_DensityDescriptor
from rhombus.language.types import range_choice
from rhombus import config

import sympy

class LogExpr: 

    def __init__(self, expression: sympy.Expr, map: dict[sympy.Symbol, DensityDescriptor]):
        self.expr: sympy.Expr = sympy.simplify(expression)
        self.map = map
   




class Condition:

    def __init__(self, logexpr: LogExpr, preceding_causality: "Causality" = None):
        self._logexpr = logexpr
        self._preceding_causality = preceding_causality

    def __and__(self, other: "Condition"):
        if self._preceding_causality is not None and other._preceding_causality is not None:
            raise Exception("Cannot combine conditions with two prefixed causalities")
        return Condition(
            logexpr=LogExpr(expression=self._logexpr.expr and other._logexpr.expr, map=self._logexpr.map | other._logexpr.map),
            preceding_causality=self._preceding_causality if self._preceding_causality is not None else other._preceding_causality
        )
    
    def __pos__(self):
        return Condition(self._logexpr, preceding_causality=self._preceding_causality)

    def then(self, value: DensityDescriptor) -> "Causality":
        return Causality(*self._preceding_causality._causalities, (self, value))
        
            

class Causality:

    def __init__(self, *causalities: tuple[Condition, DensityDescriptor]):
        self._causalities = causalities

    ...

# def when(argument: DensityDescriptor, *,
#          equals: float = ...,
#          greater: float = ...,
#          less: float = ...,
#          greaterOrEqual: float = ...,
#          lessOrEqual: float = ...,
#          between: tuple[float, float] = ...,
#          betweenInclusively: tuple[float, float] = ...,
#          unequal: float = ...
#     ) -> Condition:

#     params = {
#         "equals": equals,
#         "greater": greater,
#         "less": less,
#         "greaterOrEqual": greaterOrEqual,
#         "lessOrEqual": lessOrEqual,
#         "between": between,
#         "betweenInclusively": betweenInclusively,
#         "unequal": unequal
#     }

#     if ["given" for i in [v for k, v in params.items()] if i is not ...].count("given") != 1:
#         raise ValueError("Can only check for one condition")
    
#     type = next(k for k, v in params.items() if v is not ...)
    
#     return Condition((argument, type, params[type]))