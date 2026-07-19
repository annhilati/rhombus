"""
This module provides a fluent interface for realising conditionality by
constructing nested expressions with `range_choice` and `interval_select`.

**IMPORTANT** If the conditionality produces a density function with recurring parts,
they will automatically be cached.

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
"""

from __future__ import annotations

__all__ = ["when", "NOT", "ALL", "ANY", "it"]

from dataclasses import dataclass, field
from typing import Any, Never
from enum import Enum

from rhombus.core.density_function import DensityFunction
from rhombus.core import config
from rhombus.std.types import range_choice, interval_select, literal_number_limit
from rhombus.std.density import Density, AnyDensity

EPSILON = config.env.infinitesimal
OMEGA = literal_number_limit


class Itself:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "it"


it = Itself()
"Typing sentinel to denote, that the last specified input is reused"


class Relation(str, Enum):
    EQUALS = "=="
    UNEQUAL = "!="
    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_OR_EQUAL = "<="
    GREATER_OR_EQUAL = ">="
    INSIDE = "inside"
    OUTSIDE = "outside"
    ABOVE_BUT_UNDER = "above_under"


# ======// Condition //===========================================================================//


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

    def then(self, value: AnyDensity | Itself) -> "Causality":
        """Specifies the value that is returned, if the condition applies.

        ## Continuation
            **Append another alternative condition**
                `~.elsewhen(AnyDensity)`
            **Specify the fallback value and close the expression**
                `~.otherwise(AnyDensity)`
        """
        if value is it:
            if self._default_input is None:
                raise TypeError(
                    "then(it) is undefined because the initial condition was not composed of a condition with input"
                )
            value = self._default_input
        return Causality(
            _cases=[(self, Density(value).AST)], _default_input=self._default_input
        )

    def _compile(
        self, when_true: DensityFunction, when_false: DensityFunction
    ) -> DensityFunction:
        raise NotImplementedError(
            "No compilation procedure for generic Condition defined. This is a bug"
        )


@dataclass(frozen=True)
class ComparisonCondition(Condition):
    input: DensityFunction
    relation: Relation
    value: float | tuple[float, float]

    @property
    def _default_input(self) -> DensityFunction:
        return self.input

    def _compile(
        self, when_true: DensityFunction, when_false: DensityFunction
    ) -> DensityFunction:

        def ensure_pair(value: tuple[float, float]) -> tuple[float, float]:
            if not isinstance(value, tuple) or len(value) != 2:
                raise TypeError("expected tuple with two floats")
            a, b = float(value[0]), float(value[1])
            return (a, b) if a <= b else (b, a)

        relation = self.relation

        # Primitive case
        if relation == Relation.ABOVE_BUT_UNDER:
            low, high = ensure_pair(self.value)
            return range_choice(
                input=self.input,
                min_inclusive=max(low, -OMEGA),
                max_exclusive=min(high, OMEGA),
                when_in_range=when_true,
                when_out_of_range=when_false,
            )

        # Other
        if relation == Relation.INSIDE:
            low, high = ensure_pair(self.value)
            return ComparisonCondition(
                self.input, Relation.ABOVE_BUT_UNDER, (low, high + EPSILON)
            )._compile(when_true, when_false)

        # Unbounded relations using interval_select
        if relation == Relation.LESS_THAN:
            v = float(self.value)
            return interval_select(
                input=self.input, thresholds=[v], functions=[when_true, when_false]
            )

        if relation == Relation.LESS_OR_EQUAL:
            v = float(self.value)
            return interval_select(
                input=self.input,
                thresholds=[v + EPSILON],
                functions=[when_true, when_false],
            )

        if relation == Relation.GREATER_THAN:
            v = float(self.value)
            return interval_select(
                input=self.input,
                thresholds=[v + EPSILON],
                functions=[when_false, when_true],
            )

        if relation == Relation.GREATER_OR_EQUAL:
            v = float(self.value)
            return interval_select(
                input=self.input, thresholds=[v], functions=[when_false, when_true]
            )

        # Derived relations
        if relation == Relation.EQUALS:
            v = float(self.value)
            return ComparisonCondition(
                self.input, Relation.ABOVE_BUT_UNDER, (v, v + EPSILON)
            )._compile(when_true, when_false)

        if relation == Relation.UNEQUAL:
            v = float(self.value)
            return ComparisonCondition(
                self.input, Relation.ABOVE_BUT_UNDER, (v, v + EPSILON)
            )._compile(when_true=when_false, when_false=when_true)

        if relation == Relation.OUTSIDE:
            low, high = ensure_pair(self.value)
            return ComparisonCondition(
                self.input, Relation.ABOVE_BUT_UNDER, (low, high + EPSILON)
            )._compile(when_false=when_true, when_true=when_false)

        raise ValueError(f"Unsupported relation: {relation}")


@dataclass(frozen=True)
class AndCondition(Condition):
    left: Condition
    right: Condition

    @property
    def _default_input(self):
        return self.left._default_input or self.right._default_input

    def _compile(
        self, when_true: DensityFunction, when_false: DensityFunction
    ) -> DensityFunction:
        return self.left._compile(
            self.right._compile(when_true, when_false), when_false
        )


@dataclass(frozen=True)
class OrCondition(Condition):
    left: Condition
    right: Condition

    @property
    def _default_input(self):
        return self.left._default_input or self.right._default_input

    def _compile(
        self, when_true: DensityFunction, when_false: DensityFunction
    ) -> DensityFunction:
        return self.left._compile(when_true, self.right._compile(when_true, when_false))


@dataclass(frozen=True)
class NotCondition(Condition):
    inner: Condition

    @property
    def _default_input(self):
        return self.inner._default_input

    def _compile(
        self, when_true: DensityFunction, when_false: DensityFunction
    ) -> DensityFunction:
        return self.inner._compile(when_true=when_false, when_false=when_true)


# ======// Logical Functions //===================================================================//


def NOT(condition: Condition, /) -> Condition:
    """Negates a condition. Equivalent to `~condition`."""
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


# ======// Causality Class //=====================================================================//


@dataclass
class Causality:
    _cases: list[tuple[Condition, DensityFunction]] = field(default_factory=list)
    _default_input: DensityFunction | None = None

    def __post_init__(self):
        self.elsewhen = type(self).elsewhen()._bind(self)

    class elsewhen:
        """Specifies a fallback option for the conditionality if none of the
        preceding conditions apply. When called without arguments, the input
        of the initial condition is used.

        ## Continuation

            **`~.equals(float)`**
                `self == other`
            **`~.unequals(float)`**
                `self != other`
            **`~.greater(float)`**
                `self > other`
            **`~.less(float)`**
                `self < other`
            **`~.atleast(float)`**
                `self >= other`
            **`~.atmost(float)`**
                `self <= other`
            **`~.inside(float, float)`**
                `low <= self <= high`
            **`~.outside(float, float)`**
                `self < low` or `self > high`
            **`~.atleast_but_less(float, float)`**
                `low <= self < high`
                This is the standard case for `range_choice`.
        """

        _chain: Causality
        _subject: DensityFunction | None = None

        def __init__(self, subject: AnyDensity | Itself = it):
            self._subject = None
            self._pending_subject = subject

        def _bind(self, chain: Causality):
            self._chain = chain

            subject = self._pending_subject
            if subject is it:
                if self._chain._default_input is None:
                    raise TypeError(
                        "elsewhen(it) is undefined because the initial condition was not composed of a condition with input"
                    )
                subject = self._chain._default_input

            self._subject = Density(subject).AST
            del self._pending_subject
            return self

        def __call__(self, subject: AnyDensity | Itself = it):
            return type(self)(subject)._bind(self._chain)

        def equals(self, value: float) -> Condition:
            return OtherPendingCondition(self._chain, when(self._subject).equals(value))

        def unequals(self, value: float) -> Condition:
            return OtherPendingCondition(
                self._chain, when(self._subject).unequals(value)
            )

        def greater(self, value: float) -> Condition:
            return OtherPendingCondition(
                self._chain, when(self._subject).greater(value)
            )

        def less(self, value: float) -> Condition:
            return OtherPendingCondition(self._chain, when(self._subject).less(value))

        def atleast(self, value: float) -> Condition:
            return OtherPendingCondition(
                self._chain, when(self._subject).atleast(value)
            )

        def atmost(self, value: float) -> Condition:
            return OtherPendingCondition(self._chain, when(self._subject).atmost(value))

        def inside(self, low: float, high: float, /) -> Condition:
            return OtherPendingCondition(
                self._chain, when(self._subject).inside(low, high)
            )

        def atleast_but_less(self, low: float, high: float, /) -> Condition:
            return OtherPendingCondition(
                self._chain, when(self._subject).atleast_but_less(low, high)
            )

        def outside(self, low: float, high: float, /) -> Condition:
            return OtherPendingCondition(
                self._chain, when(self._subject).outside(low, high)
            )

    def otherwise(self, value: AnyDensity | Itself) -> Density[range_choice]:
        """Specified a fallback value that is returned if none of the conditions apply.

        Returns:
            Density: The resulting density function representing the entire conditionality expression.
        """
        from rhombus.macros.performance import s_cache_transform

        if value is it:
            if self._default_input is None:
                raise TypeError(
                    "otherwise(it) is undefined because the initial condition was not composed of a condition with input"
                )
            value = self._default_input
        result = Density(value).AST
        for condition, branch_value in reversed(self._cases):
            result = condition._compile(branch_value, result)
        return s_cache_transform(Density(result), self._default_input or None)


@dataclass
class OtherPendingCondition:
    _chain: Causality
    _condition: Condition

    def then(self, value: AnyDensity | Itself) -> Causality:
        """Specifies the value that is returned, if the condition applies.

        ## Continuation
            **Append another alternative condition**
                `~.elsewhen(AnyDensity)`
            **Specify the fallback value and close the expression**
                `~.otherwise(AnyDensity)`
        """
        if value is it:
            if self._chain._default_input is None:
                raise TypeError(
                    "then(it) is undefined because the initial condition was not composed of a condition with input"
                )
            value = self._chain._default_input
        self._chain._cases.append((self._condition, Density(value).AST))
        return self._chain


# ======// Condition Fabric //====================================================================//


class when:
    """Opens a new conditionality fluent interface.

    To continue, use one  of the following methods to specify the condition:
    ## Continuation

        **`~.equals(float)`**
            `self == other`
        **`~.unequals(float)`**
            `self != other`
        **`~.greater(float)`**
            `self > other`
        **`~.less(float)`**
            `self < other`
        **`~.atleast(float)`**
            `self >= other`
        **`~.atmost(float)`**
            `self <= other`
        **`~.inside(float, float)`**
            `low <= self <= high`
        **`~.outside(float, float)`**
            `self < low` or `self > high`
        **`~.atleast_but_less(float, float)`**
            `low <= self < high`
            This is the standard case for `range_choice`.
    """

    _subject: DensityFunction

    def __init__(self, subject: AnyDensity):
        self._subject = Density(subject).AST

    def equals(self, value: float) -> Condition:
        return ComparisonCondition(
            input=self._subject, relation=Relation.EQUALS, value=value
        )

    def unequals(self, value: float) -> Condition:
        return ComparisonCondition(
            input=self._subject, relation=Relation.UNEQUAL, value=value
        )

    def greater(self, value: float) -> Condition:
        return ComparisonCondition(
            input=self._subject, relation=Relation.GREATER_THAN, value=value
        )

    def less(self, value: float) -> Condition:
        return ComparisonCondition(
            input=self._subject, relation=Relation.LESS_THAN, value=value
        )

    def atleast(self, value: float) -> Condition:
        return ComparisonCondition(
            input=self._subject, relation=Relation.GREATER_OR_EQUAL, value=value
        )

    def atmost(self, value: float) -> Condition:
        return ComparisonCondition(
            input=self._subject, relation=Relation.LESS_OR_EQUAL, value=value
        )

    def inside(self, low: float, high: float, /) -> Condition:
        return ComparisonCondition(
            input=self._subject, relation=Relation.INSIDE, value=(low, high)
        )

    def atleast_but_less(self, low: float, high: float, /) -> Condition:
        return ComparisonCondition(
            input=self._subject, relation=Relation.ABOVE_BUT_UNDER, value=(low, high)
        )

    def outside(self, low: float, high: float, /) -> Condition:
        return ComparisonCondition(
            input=self._subject, relation=Relation.OUTSIDE, value=(low, high)
        )
