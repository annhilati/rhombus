"""
This module provides a basic fluent interface for realising conditionality
with `range_choice` expressions.

The syntax goes like this:
```
from rhombus.std.conditional import *

out = (
    when(input).equals(1.0)
        .then(10.0)
    .elsewhen(it).equals(2.0)
        .then(20.0)
    .otherwise(0.0)
)
```

Please note, that using conditionality with large density function trees as
inputs can inflate the resulting density function significantly. In such
cases, algebraic methods should be used whenever possible.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, SupportsIndex, Never, ClassVar
from enum import Enum

from rhombus.core.density_function import DensityFunction
from rhombus.std.types import range_choice, constant_number_limit
from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro
from rhombus import config

EPSILON = config.infinitesimal
INFINITY = constant_number_limit

__all__ = [
    "when", "NOT", "ALL", "ANY", "it"
]

def _ensure_pair(value: SupportsIndex) -> tuple[float, float]:
    if not isinstance(value, tuple) or len(value) != 2:
        raise TypeError("expected tuple with two floats")
    a, b = float(value[0]), float(value[1])
    return (a, b) if a <= b else (b, a)


# TODO make this a genuine singleton sentinel
class Itself:
    pass

it = Itself()
"Typing sentinel to denote, that the last specified input is reused"

class Relation(str, Enum):
    EQUALS = "=="
    UNEQUAL = "!="
    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_OR_EQUAL = "<="
    GREATER_OR_EQUAL = ">="
    BETWEEN = "between"
    OUTSIDE = "outside"


#======// Condition //===========================================================================//

class Condition:

    def __and__(self, other: Condition) -> Condition:
        return AndCondition(self, other)

    def __rand__(self, other: Condition) -> Condition:
        return AndCondition(other, self)

    def __or__(self, other: Condition) -> Condition:
        return OrCondition(self, other)

    def __ror__(self, other: Condition) -> Condition:
        return OrCondition(other, self)

    def __invert__(self) -> Condition:
        return NotCondition(self)

    def __bool__(self) -> Never:
        raise TypeError(
            "Condition object cannot be used as bool. "
            "If you tried using Conditions with the 'and', 'or' or 'not' operator, "
            "use the bitwise '&', '|' or '~' operator instead"
        )
    
    @property
    def _default_input(self) -> Any:
        return None

    def then(self, value: AnyDensity) -> "Causality":
        """Specifies the value that is returned, if the condition applies.
        
        ## Continuation
            **Append another alternative condition**
                `~.elsewhen(AnyDensity)`
            **Specify the fallback value and close the expression**
                `~.otherwise(AnyDensity)`
        """
        return Causality(
            _cases=[(self, Density.constant(value).AST)],
            _default_input=self._default_input
)

    def _compile(self, when_true: DensityFunction, when_false: DensityFunction) -> DensityFunction:
        raise NotImplementedError("No compilation procedure for generic Condition defined. This is a bug")

@dataclass(frozen=True)
class ComparisonCondition(Condition):
    input: DensityFunction
    relation: Relation
    value: float | tuple[float, float]

    @property
    def _default_input(self) -> DensityFunction:
        return self.input

    def _compile(self, when_true: DensityFunction, when_false: DensityFunction) -> DensityFunction:
        relation = self.relation

        # Primitive case
        if relation == Relation.BETWEEN:
            low, high = _ensure_pair(self.value)
            return range_choice(
                input=self.input,
                min_inclusive=max(low, -INFINITY),
                max_exclusive=min(high + EPSILON, INFINITY),
                when_in_range=when_true,
                when_out_of_range=when_false
            )

        # Other
        if relation == Relation.LESS_THAN:
            v = float(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (-INFINITY, v - EPSILON))._compile(when_true, when_false)

        if relation == Relation.LESS_OR_EQUAL:
            v = float(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (-INFINITY, v))._compile(when_true, when_false)

        if relation == Relation.GREATER_THAN:
            v = float(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (v + EPSILON, INFINITY))._compile(when_true, when_false)

        if relation == Relation.GREATER_OR_EQUAL:
            v = float(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (v, INFINITY))._compile(when_true, when_false)

        # Derived relations
        if relation == Relation.EQUALS:
            v = float(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (v, v + EPSILON))._compile(when_true, when_false)

        if relation == Relation.UNEQUAL:
            v = float(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (v, v + EPSILON))._compile(when_true=when_false, when_false=when_true)

        if relation == Relation.OUTSIDE:
            low, high = _ensure_pair(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (low, high + EPSILON))._compile(when_false=when_true, when_true=when_false)

        raise ValueError(f"Unsupported relation: {relation}")


@dataclass(frozen=True)
class AndCondition(Condition):
    left: Condition
    right: Condition

    def _compile(self, when_true: DensityFunction, when_false: DensityFunction) -> DensityFunction:
        return self.left._compile(self.right._compile(when_true, when_false), when_false)


@dataclass(frozen=True)
class OrCondition(Condition):
    left: Condition
    right: Condition

    def _compile(self, when_true: DensityFunction, when_false: DensityFunction) -> DensityFunction:
        return self.left._compile(when_true, self.right._compile(when_true, when_false))

@dataclass(frozen=True)
class NotCondition(Condition):
    inner: Condition

    def _compile(self, when_true: DensityFunction, when_false: DensityFunction) -> DensityFunction:
        return self.inner._compile(when_true=when_false, when_false=when_true)


#======// Logical Functions //===================================================================//

def NOT(condition: Condition, /) -> Condition:
    """Negates a condition. Equivalent to `~condition`.
    """
    return ~condition

def ALL(*conditions: Condition) -> Condition:
    """Combines multiple conditions with a logical AND.
    Equivalent to `condition1 & condition2`.
    """
    if not conditions:
        raise ValueError("ALL() requires at least one condition")
    result = conditions[0]
    for cond in conditions[1:]:
        result = result & cond
    return result

def ANY(*conditions: Condition) -> Condition:
    """Combines multiple conditions with a logical OR.
    Equivalent to `condition1 | condition2`.
    """
    if not conditions:
        raise ValueError("ANY() requires at least one condition")
    result = conditions[0]
    for cond in conditions[1:]:
        result = result | cond
    return result


#======// Causality Class //=====================================================================//

@dataclass
class Causality:
    _cases: list[tuple[Condition, DensityFunction]] = field(default_factory=list)
    _default_input: DensityFunction | None = None

    def __post_init__(self):
        self.elsewhen._chain = self

    class elsewhen:
        """Specifies a fallback option for the conditionality if none of the preceding
        conditions apply. When called without arguments, the input of the initial condition is used.

        ## Continuation

        **Equal to**  
            `~.equals(float)`
        **Unequal to**  
            `~.unequal(float)`
        **Greater than**  
            `~.greater(float)`
        **Less than**  
            `~.less(float)`
        **Greater or equal**  
            `~.greatereq(float)`
        **Less or equal**  
            `~.lesseq(float)`
        **Between**  
            `~.between(float, float)`
        **Outside of**  
            `~.outside(float, float)`
        """
        _subject: DensityFunction
        _chain: ClassVar[Causality] = ...

        def __init__(self, subject: AnyDensity | Itself = it):
            if subject is it:
                if self._chain._default_input is None:
                    raise TypeError("elsewhen() with implicit input is only possible if the initial condition is not composed of multiple conditions")
                subject = self._chain._default_input
            self._subject = Density.constant(subject).AST

        def equals(self, value: float) -> Condition:
            return OtherPendingCondition(self._chain, when(self._subject).equals(value))
        def unequal(self, value: float) -> Condition:
            return OtherPendingCondition(self._chain, when(self._subject).unequal(value))
        def greater(self, value: float) -> Condition:
            return OtherPendingCondition(self._chain, when(self._subject).greater(value))
        def less(self, value: float) -> Condition:
            return OtherPendingCondition(self._chain, when(self._subject).less(value))
        def greatereq(self, value: float) -> Condition:
            return OtherPendingCondition(self._chain, when(self._subject).greatereq(value))
        def lesseq(self, value: float) -> Condition:
            return OtherPendingCondition(self._chain, when(self._subject).lesseq(value))
        def between(self, low: float, high: float, /) -> Condition:
            return OtherPendingCondition(self._chain, when(self._subject).between(low, high))
        def outside(self, low: float, high: float, /) -> Condition:
            return OtherPendingCondition(self._chain, when(self._subject).outside(low, high))
        

    def otherwise(self, value: AnyDensity) -> Density[range_choice]:
        """Specified a fallback value that is returned if none of the conditions apply.
        
        Returns:
            Density: The resulting density function representing the entire conditionality expression.
        """
        result = Density.constant(value).AST
        for condition, branch_value in reversed(self._cases):
            result = condition._compile(branch_value, result)
        return Density(result)


@dataclass
class OtherPendingCondition:
    _chain: Causality
    _condition: Condition

    def then(self, value: AnyDensity) -> Causality:
        """Specifies the value that is returned, if the condition applies.
        
        ## Continuation
            **Append another alternative condition**
                `~.elsewhen(AnyDensity)`
            **Specify the fallback value and close the expression**
                `~.otherwise(AnyDensity)`
        """
        self._chain._cases.append((self._condition, Density.constant(value).AST))
        return self._chain


#======// Condition Fabric //====================================================================//

class when:
    """Opens a new conditionality fluent interface. 
    
    To continue, use one  of the following methods to specify the condition:
    ## Continuation

        **Equal to**  
            `~.equals(float)`
        **Unequal to**  
            `~.unequal(float)`
        **Greater than**  
            `~.greater(float)`
        **Less than**  
            `~.less(float)`
        **Greater or equal**  
            `~.greatereq(float)`
        **Less or equal**  
            `~.lesseq(float)`
        **Between**  
            `~.between(float, float)`
        **Outside of**  
            `~.outside(float, float)`
    """
    _subject: DensityFunction

    @macro
    def __init__(self, subject: AnyDensity):
        self._subject = subject.AST


    def equals(self, value: float) -> Condition:
        return ComparisonCondition(input=self._subject, relation=Relation.EQUALS, value=value)
    def unequal(self, value: float) -> Condition:
        return ComparisonCondition(input=self._subject, relation=Relation.UNEQUAL, value=value)
    def greater(self, value: float) -> Condition:
        return ComparisonCondition(input=self._subject, relation=Relation.GREATER_THAN, value=value)
    def less(self, value: float) -> Condition:
        return ComparisonCondition(input=self._subject, relation=Relation.LESS_THAN, value=value)
    def greatereq(self, value: float) -> Condition:
        return ComparisonCondition(input=self._subject, relation=Relation.GREATER_OR_EQUAL, value=value)
    def lesseq(self, value: float) -> Condition:
        return ComparisonCondition(input=self._subject, relation=Relation.LESS_OR_EQUAL, value=value)
    def between(self, low: float, high: float, /) -> Condition:
        return ComparisonCondition(input=self._subject, relation=Relation.BETWEEN, value=(low, high))
    def outside(self, low: float, high: float, /) -> Condition:
        return ComparisonCondition(input=self._subject, relation=Relation.OUTSIDE, value=(low, high))