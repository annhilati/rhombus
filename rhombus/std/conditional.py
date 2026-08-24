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
from rhombus.std.density import Density, AnyDensity; from rhombus.std.macros import macro; from rhombus.std import caching
from rhombus.support import vanilla as vt

from rhombus.core.environment import env

EPSILON = env.infinitesimal
OMEGA = vt.literal_number_limit


# ======// Vanilla Coverage //====================================================================//


# IDEA: Move this
@macro
def range_choice(
    input: AnyDensity,
    min_inclusive: float,
    max_exclusive: float,
    when_in_range: AnyDensity,
    when_out_of_range: AnyDensity,
) -> Density[vt.range_choice]:
    """Computes the input value, and depending on that result returns one of two other density functions. Basically an if-then-else statement.

    **NOTE:** To create logic or conditional expressions, use `rhombus.macros.conditional`.

    ```
    if input >= min_inclucive:
        if input < max_exclusive:
            return when_in_range
    return when_out_of_range
    ```

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#range_choice)
    """
    return Density(
        vt.range_choice(
            input.AST,
            min_inclusive,
            max_exclusive,
            when_in_range.AST,
            when_out_of_range.AST,
        )
    )


@macro
def interval_select(
    input: AnyDensity, thresholds: list[float], functions: list[AnyDensity]
):
    """Selects between a number of density functions based on an input density function and a set of threshold values.

    Parameters:
        input (density function): Density Function, to be compared with given thresholds.
        thresholds (list[float]):  Threshold values to compare input with. Must be non-empty.
            If `input < thresholds[i]`, `functions[i]` will be selected. If the input is greater than the last threshold value, the last function will be selected.
            Must be one fewer thresholds than functions.
        functions (list[density function]): List of density functions to be selected from. Must be one more element in functions than in thresholds.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#interval_select)
    """
    return Density(
        vt.interval_select(
            input.AST, thresholds, [function.AST for function in functions]
        )
    )


# ======// Conditionality Fluent Interface //=====================================================//


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
            return vt.range_choice(
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

        # Unbounded relations using interval_select or range_choice fallback
        if relation == Relation.LESS_THAN:
            v = float(self.value)
            if vt.interval_select.is_active(env):
                return vt.interval_select(
                    input=self.input, thresholds=[v], functions=[when_true, when_false]
                )
            return vt.range_choice(self.input, -OMEGA, v, when_true, when_false)

        if relation == Relation.LESS_OR_EQUAL:
            v = float(self.value)
            if vt.interval_select.is_active(env):
                return vt.interval_select(
                    input=self.input,
                    thresholds=[v + EPSILON],
                    functions=[when_true, when_false],
                )
            return vt.range_choice(self.input, -OMEGA, v + EPSILON, when_true, when_false)

        if relation == Relation.GREATER_THAN:
            v = float(self.value)
            if vt.interval_select.is_active(env):
                return vt.interval_select(
                    input=self.input,
                    thresholds=[v + EPSILON],
                    functions=[when_false, when_true],
                )
            return vt.range_choice(self.input, -OMEGA, v + EPSILON, when_false, when_true)

        if relation == Relation.GREATER_OR_EQUAL:
            v = float(self.value)
            if vt.interval_select.is_active(env):
                return vt.interval_select(
                    input=self.input, thresholds=[v], functions=[when_false, when_true]
                )
            return vt.range_choice(self.input, -OMEGA, v, when_false, when_true)

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


# ======// Condition Builder //===================================================================//


class _ConditionBuilder[T]:
    _subject: DensityFunction

    def _wrap(self, cond: Condition) -> T:
        raise NotImplementedError

    def equals(self, value: float) -> T:
        return self._wrap(
            ComparisonCondition(
                input=self._subject, relation=Relation.EQUALS, value=value
            )
        )

    def unequals(self, value: float) -> T:
        return self._wrap(
            ComparisonCondition(
                input=self._subject, relation=Relation.UNEQUAL, value=value
            )
        )

    def greater(self, value: float) -> T:
        return self._wrap(
            ComparisonCondition(
                input=self._subject, relation=Relation.GREATER_THAN, value=value
            )
        )

    def less(self, value: float) -> T:
        return self._wrap(
            ComparisonCondition(
                input=self._subject, relation=Relation.LESS_THAN, value=value
            )
        )

    def atleast(self, value: float) -> T:
        return self._wrap(
            ComparisonCondition(
                input=self._subject, relation=Relation.GREATER_OR_EQUAL, value=value
            )
        )

    def atmost(self, value: float) -> T:
        return self._wrap(
            ComparisonCondition(
                input=self._subject, relation=Relation.LESS_OR_EQUAL, value=value
            )
        )

    def inside(self, low: float, high: float, /) -> T:
        return self._wrap(
            ComparisonCondition(
                input=self._subject, relation=Relation.INSIDE, value=(low, high)
            )
        )

    def atleast_but_less(self, low: float, high: float, /) -> T:
        return self._wrap(
            ComparisonCondition(
                input=self._subject,
                relation=Relation.ABOVE_BUT_UNDER,
                value=(low, high),
            )
        )

    def outside(self, low: float, high: float, /) -> T:
        return self._wrap(
            ComparisonCondition(
                input=self._subject, relation=Relation.OUTSIDE, value=(low, high)
            )
        )

    def is_nan(self) -> T:
        return self._wrap(
            ~(
                when(self._subject).less(0)
                | when(vt.mul(self._subject, vt.constant(-1.0))).less(0)
                | when(self._subject).inside(-0.1, 0.1)
            )
        )

    def is_infinite(self) -> T:
        return self._wrap(
            when(vt.mul(self._subject, vt.constant(0.0))).unequals(0.0)
            & (
                when(self._subject).less(0)
                | when(vt.mul(self._subject, vt.constant(-1.0))).less(0)
            )
        )


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


# ======// Causality Class //=====================================================================//


@dataclass
class Causality:
    _cases: list[tuple[Condition, DensityFunction]] = field(default_factory=list)
    _default_input: DensityFunction | None = None

    def __post_init__(self):
        self.elsewhen = type(self).elsewhen()._bind(self)

    class elsewhen(_ConditionBuilder[OtherPendingCondition]):
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
            **`~.is_nan()`**
                `self == NaN`
            **`~.is_infinite()`**
                `self == +Infinity` or `self == -Infinity`
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

        def _wrap(self, cond: Condition) -> OtherPendingCondition:
            return OtherPendingCondition(self._chain, cond)

    def otherwise(
        self, value: AnyDensity | Itself = it
    ) -> Density[vt.range_choice | vt.interval_select]:
        """Specified a fallback value that is returned if none of the conditions apply.

        Returns:
            Density: The resulting density function representing the entire conditionality expression.
        """
        if value is it:
            if self._default_input is None:
                raise TypeError(
                    "otherwise(it) is undefined because the initial condition was not composed of a singular condition with input"
                )
            value = self._default_input
        result = Density(value).AST
        for condition, branch_value in reversed(self._cases):
            result = condition._compile(branch_value, result)
        default_input = Density(self._default_input) if self._default_input is not None else None
        return caching.specified_cache(Density(result), default_input)


# ======// Condition Fabric //====================================================================//


class when(_ConditionBuilder[Condition]):
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
        **`~.is_nan()`**
            `self == NaN`
        **`~.is_infinite()`**
            `self == +Infinity` or `self == -Infinity`
    """

    _subject: DensityFunction

    def __init__(self, subject: AnyDensity):
        self._subject = Density(subject).AST

    def _wrap(self, cond: Condition) -> Condition:
        return cond
