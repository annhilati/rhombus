from typing import overload, Literal, Callable
from rhombus.language import Density, DensityDescriptor, resolve_DensityDescriptor
from rhombus.language.types import range_choice
from rhombus import config

__all__ = ["when"]


class Condition:


    # @overload
    # def __init__(self, *conditions: tuple[DensityDescriptor, Literal["equals", "greater", "less", "greaterOrEqual", "lessOrEqual", "unequal"], float]): ...
    # @overload
    # def __init__(self, *conditions: tuple[DensityDescriptor, Literal["between", "betweenInclusively"], tuple[float, float]]): ...
    
    def __init__(self,
            *conditions: tuple[DensityDescriptor, str, float | tuple[float, float]],
            preceding_causality: "Causality" = None):
        self._conditions = [c for c in conditions]
        self._preceding_causality = preceding_causality

    def __and__(self, other: "Condition"):
        if len(self._preceding_causality) != None:
            raise Exception("Cannot combine conditions with already defined consequences")
        return Condition(*self._conditions, *other._conditions)
    
    def __or__(self, other: "Condition"):


    def then(self, value: DensityDescriptor) -> "Causality":
        "Next step: `.otherwise()`"
        return Causality(condition=self, consequence=value, preceding_causalities=self._preceding_causality)
    
    # @property
    # def _factory(self) -> Callable[[DensityDescriptor, tuple["Condition", DensityDescriptor],DensityDescriptor], Density]:

    #     if len(self._conditions) == 0:
    #         raise Exception
            
    #     current: Callable[[DensityDescriptor, tuple[tuple[Condition, DensityDescriptor]], DensityDescriptor], Density] | None = None

    #     for condition in reversed(self._conditions):
    #         arg, type, value = condition
    #         arg = resolve_DensityDescriptor(arg).AST

    #         match type:
    #             case "equals":
    #                 def fn(then: DensityDescriptor, *butifs: tuple[Condition, DensityDescriptor], otherwise: DensityDescriptor) -> Density[range_choice]:
    #                     if len(butifs) > 0:
    #                         next_butif = next(iter(butifs))
    #                     return Density(range_choice(
    #                         input=arg,
    #                         min_inclusive=value,
    #                         max_exclusive=value + 1/config.constant_number_limit,
    #                         when_in_range=resolve_DensityDescriptor(then),
    #                         when_out_of_range=otherwise if len(butifs) == 0 else next_butif[0]._factory(next_butif[1], (b for b in butifs if b != butifs[0]), otherwise)
    #                     ))
                        
                    
    #                 current = fn if current is None else fn()


        # input = resolve_DensityDescriptor(self._argument).AST

        # match self._relationship: 
        #     case "equals":
        #         return lambda then, otherwise: Density(range_choice(
        #             input=input,
        #             min_inclusive=float(self._value),
        #             max_exclusive=float(self._value) + 1/config.constant_number_limit,
        #             when_in_range=resolve_DensityDescriptor(then).AST,
        #             when_out_of_range=resolve_DensityDescriptor(otherwise).AST
        #         ))
            # case "greater":
            #     return lambda then, otherwise: Density(range_choice(
            #         input=input,
            #         min_inclusive=-config.constant_number_limit,
            #         max_exclusive=float(self._value),
            #         when_in_range=resolve_DensityDescriptor(otherwise).AST, # we swapped here
            #         when_out_of_range=resolve_DensityDescriptor(then).AST
            #     ))
            # case "less":
            #     return lambda then, otherwise: Density(range_choice(
            #         input=input,
            #         min_inclusive=float(self._value),
            #         max_exclusive=config.constant_number_limit,
            #         when_in_range=resolve_DensityDescriptor(otherwise).AST, # we swapped here
            #         when_out_of_range=resolve_DensityDescriptor(then).AST
            #     ))
            # case "greaterOrEqual":
            #     return lambda then, otherwise: Density(range_choice(
            #         input=input,
            #         min_inclusive=float(self._value),
            #         max_exclusive=config.constant_number_limit,
            #         when_in_range=resolve_DensityDescriptor(then).AST,
            #         when_out_of_range=resolve_DensityDescriptor(otherwise).AST
            #     ))
            # case "lessOrEqual":
            #     return lambda then, otherwise: Density(range_choice(
            #         input=input,
            #         min_inclusive=-config.constant_number_limit,
            #         max_exclusive=float(self._value) + 1/config.constant_number_limit,
            #         when_in_range=resolve_DensityDescriptor(then).AST,
            #         when_out_of_range=resolve_DensityDescriptor(otherwise).AST
            #     ))
            # case "between":
            #     range = tuple(sorted(self._value))
            #     return lambda then, otherwise: Density(range_choice(
            #         input=input,
            #         min_inclusive=float(range[0]) + 1/config.constant_number_limit,
            #         max_exclusive=float(range[1]),
            #         when_in_range=resolve_DensityDescriptor(then).AST,
            #         when_out_of_range=resolve_DensityDescriptor(otherwise).AST
            #     ))
            # case "betweenInclusively":
            #     range = tuple(sorted(self._value))
            #     return lambda then, otherwise: Density(range_choice(
            #         input=input,
            #         min_inclusive=float(range[0]),
            #         max_exclusive=float(range[1]) + 1/config.constant_number_limit,
            #         when_in_range=resolve_DensityDescriptor(then).AST,
            #         when_out_of_range=resolve_DensityDescriptor(otherwise).AST
            #     ))
            # case "unequal":
            #     return lambda then, otherwise: Density(range_choice(
            #         input=input,
            #         min_inclusive=float(self._value),
            #         max_exclusive=float(self._value) + 1/config.constant_number_limit,
            #         when_in_range=resolve_DensityDescriptor(otherwise).AST, # we swapped here
            #         when_out_of_range=resolve_DensityDescriptor(then).AST
            #     ))
                # case _:
                #     raise ValueError
        
            

def when(argument: DensityDescriptor, *,
         equals: float = ...,
         greater: float = ...,
         less: float = ...,
         greaterOrEqual: float = ...,
         lessOrEqual: float = ...,
         between: tuple[float, float] = ...,
         betweenInclusively: tuple[float, float] = ...,
         unequal: float = ...
    ) -> Condition:
    "Next step: `.then()`"

    params = {
        "equals": equals,
        "greater": greater,
        "less": less,
        "greaterOrEqual": greaterOrEqual,
        "lessOrEqual": lessOrEqual,
        "between": between,
        "betweenInclusively": betweenInclusively,
        "unequal": unequal
    }

    if ["given" for i in [v for k, v in params.items()] if i is not ...].count("given") != 1:
        raise ValueError("Can only check for one condition")
    
    type = next(k for k, v in params.items() if v is not ...)
    
    return Condition((argument, type, params[type]))

class Causality:

    def __init__(self, condition: Condition, consequence: DensityDescriptor, preceding_causalities: tuple["Causality", ...]):
        self._condition = condition
        self._consequence = consequence
        self._preceding_causalities = preceding_causalities

    def elsewhen(self, *,
        equals: float = ...,
        greater: float = ...,
        less: float = ...,
        greaterOrEqual: float = ...,
        lessOrEqual: float = ...,
        between: tuple[float, float] = ...,
        betweenInclusively: tuple[float, float] = ...,
        unequal: float = ...
        ) -> "Causality":

        params = {
            "equals": equals,
            "greater": greater,
            "less": less,
            "greaterOrEqual": greaterOrEqual,
            "lessOrEqual": lessOrEqual,
            "between": between,
            "betweenInclusively": betweenInclusively,
            "unequal": unequal
        }

        if ["given" for i in [v for k, v in params.items()] if i is not ...].count("given") != 1:
            raise ValueError("Can only check for one condition")
        
        type = next(k for k, v in params.items() if v is not ...)
        return Condition((self._condition.))
 
    def otherwise(self, value: DensityDescriptor):
        return self._condition._factory(self._consequence, value)

