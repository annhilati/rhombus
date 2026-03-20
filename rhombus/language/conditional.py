from typing import Literal, overload, Callable, Any
from rhombus.language import Density, DensityDescriptor, resolve_DensityDescriptor
from rhombus.language.types import range_choice
from rhombus import config

class Condition:

    def __init__(self,
        argument: DensityDescriptor,
        relationship: Literal["equals", "greater", "less", "greaterOrEqual", "lessOrEqual", "between", "betweenInclusively", "unequal"],
        value: Any
    ):
        self._argument = argument
        self._relationship = relationship
        self._value = value


    @property
    def _factory(self) -> Callable[[DensityDescriptor, DensityDescriptor], Density]:
        input = resolve_DensityDescriptor(self._argument).AST

        match self._relationship: 
            case "equals":
                return lambda then, otherwise: Density(range_choice(
                    input=input,
                    min_inclusive=float(self._value),
                    max_exclusive=float(self._value) + 1/config.constant_number_limit,
                    when_in_range=resolve_DensityDescriptor(then).AST,
                    when_out_of_range=resolve_DensityDescriptor(otherwise).AST
                ))
            case "greater":
                return lambda then, otherwise: Density(range_choice(
                    input=input,
                    min_inclusive=-config.constant_number_limit,
                    max_exclusive=float(self._value),
                    when_in_range=resolve_DensityDescriptor(otherwise).AST, # we swapped here
                    when_out_of_range=resolve_DensityDescriptor(then).AST
                ))
            case "less":
                return lambda then, otherwise: Density(range_choice(
                    input=input,
                    min_inclusive=float(self._value),
                    max_exclusive=config.constant_number_limit,
                    when_in_range=resolve_DensityDescriptor(otherwise).AST, # we swapped here
                    when_out_of_range=resolve_DensityDescriptor(then).AST
                ))
            case "greaterOrEqual":
                return lambda then, otherwise: Density(range_choice(
                    input=input,
                    min_inclusive=float(self._value),
                    max_exclusive=config.constant_number_limit,
                    when_in_range=resolve_DensityDescriptor(then).AST,
                    when_out_of_range=resolve_DensityDescriptor(otherwise).AST
                ))
            case "lessOrEqual":
                return lambda then, otherwise: Density(range_choice(
                    input=input,
                    min_inclusive=-config.constant_number_limit,
                    max_exclusive=float(self._value) + 1/config.constant_number_limit,
                    when_in_range=resolve_DensityDescriptor(then).AST,
                    when_out_of_range=resolve_DensityDescriptor(otherwise).AST
                ))
            case "between":
                range = tuple(sorted(self._value))
                return lambda then, otherwise: Density(range_choice(
                    input=input,
                    min_inclusive=float(range[0]) + 1/config.constant_number_limit,
                    max_exclusive=float(range[1]),
                    when_in_range=resolve_DensityDescriptor(then).AST,
                    when_out_of_range=resolve_DensityDescriptor(otherwise).AST
                ))
            case "betweenInclusively":
                range = tuple(sorted(self._value))
                return lambda then, otherwise: Density(range_choice(
                    input=input,
                    min_inclusive=float(range[0]),
                    max_exclusive=float(range[1]) + 1/config.constant_number_limit,
                    when_in_range=resolve_DensityDescriptor(then).AST,
                    when_out_of_range=resolve_DensityDescriptor(otherwise).AST
                ))
            case _:
                raise ValueError
        
            
    def then(self, then: DensityDescriptor) -> "Consequence":
        "Next step: `.otherwise()`"
        return Consequence(condition=self, then=then)


class Consequence:

    def __init__(self, condition: Condition, then: DensityDescriptor):
        self._condition = condition
        self._then = then
 
    def otherwise(self, value: DensityDescriptor):
        return self._condition._factory(self._then, value)


def when(argument: DensityDescriptor, *,
         equals: float = ...,
         greater: float = ...,
         less: float = ...,
         greaterOrEqual: float = ...,
         lessOrEqual: float = ...,
         between: tuple[float, float] = ...,
         betweenInclusively: tuple[float, float] = ...,
    ) -> Condition:
    "Next step: `.then()`"

    params = {
        "equals": equals,
        "greater": greater,
        "less": less,
        "greaterOrEqual": greaterOrEqual,
        "lessOrEqual": lessOrEqual,
        "between": between,
        "betweenInclusively": betweenInclusively
    }

    if ["given" for i in [v for k, v in params.items()] if i is not ...].count("given") != 1:
        raise ValueError("Can only check for one condition")
    
    type = next(k for k, v in params.items() if v is not ...)
    
    return Condition(argument=argument, relationship=type, value=params[type])