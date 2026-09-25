from __future__ import annotations

__all__ = ["when", "NOT", "ALL", "ANY", "it"]

from dataclasses import dataclass, field
from typing import Any, Never
from enum import Enum

from rhombus.core.density_function import DensityFunction
from rhombus.std.density import Density, AnyDensity
from rhombus.std import caching
import rhombus.support.vanilla.types as vt

from .macros import range_choice, interval_select

EPSILON = 1e-7
OMEGA = vt.literal_number_limit

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
            "Conditions can not be evaluated as a normal boolean value on the top level of a file. "
            "To use if/else syntax directly, make sure to only use it inside a function decorated with @macro."
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

    def __post_init__(self):
        from rhombus.core.density_function import DensityFunction
        from rhombus.std.density import Density
        
        def check_val(v):
            if isinstance(v, (DensityFunction, Density)):
                raise TypeError(
                    "Density Functions can only be conditionally compared against constants (numbers), "
                    f"not other Density Functions. Attempted to compare against: {v}"
                )
            try:
                float(v)
            except (TypeError, ValueError):
                raise TypeError(f"Comparison value must be a number, got: {type(v).__name__}")
                
        if isinstance(self.value, tuple):
            for v in self.value:
                check_val(v)
        else:
            check_val(self.value)

    @property
    def _default_input(self) -> DensityFunction:
        return self.input

    def _compile(
        self, when_true: DensityFunction, when_false: DensityFunction
    ) -> DensityFunction:

        def ensure_pair(value: float | tuple[float, float]) -> tuple[float, float]:
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
            ).AST

        # Other
        if relation == Relation.INSIDE:
            low, high = ensure_pair(self.value)
            return ComparisonCondition(
                self.input, Relation.ABOVE_BUT_UNDER, (low, high + EPSILON)
            )._compile(when_true, when_false)

        # Unbounded relations using interval_select macro
        if relation == Relation.LESS_THAN:
            v = float(self.value) # type: ignore
            return interval_select(
                input=self.input, thresholds=[v], functions=[when_true, when_false]
            ).AST

        if relation == Relation.LESS_OR_EQUAL:
            v = float(self.value) # type: ignore
            return interval_select(
                input=self.input,
                thresholds=[v + EPSILON],
                functions=[when_true, when_false],
            ).AST

        if relation == Relation.GREATER_THAN:
            v = float(self.value) # type: ignore
            return interval_select(
                input=self.input,
                thresholds=[v + EPSILON],
                functions=[when_false, when_true],
            ).AST

        if relation == Relation.GREATER_OR_EQUAL:
            v = float(self.value) # type: ignore
            return interval_select(
                input=self.input, thresholds=[v], functions=[when_false, when_true]
            ).AST

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

    def elsewhen(self, subject: AnyDensity | Itself = it) -> "_ConditionBuilder[OtherPendingCondition]":
        """Specifies a fallback option for the conditionality if none of the
        preceding conditions apply. When called without arguments, the input
        of the initial condition is used.
        """
        if subject is it:
            if self._default_input is None:
                raise TypeError(
                    "elsewhen(it) is undefined because the initial condition was not composed of a condition with input"
                )
            subject = self._default_input

        return _ElseWhenBuilder(self, Density(subject).AST)

    def otherwise(
        self, value: AnyDensity | Itself = it
    ) -> Density:
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


class _ElseWhenBuilder(_ConditionBuilder[OtherPendingCondition]):
    def __init__(self, chain: Causality, subject: DensityFunction):
        self._chain = chain
        self._subject = subject

    def _wrap(self, cond: Condition) -> OtherPendingCondition:
        return OtherPendingCondition(self._chain, cond)


# ======// Condition Fabric //====================================================================//


class _WhenBuilder(_ConditionBuilder[Condition]):
    def __init__(self, subject: DensityFunction):
        self._subject = subject

    def _wrap(self, cond: Condition) -> Condition:
        return cond


def when(subject: AnyDensity) -> _ConditionBuilder[Condition]:
    """Opens a new conditionality fluent interface."""
    return _WhenBuilder(Density(subject).AST)
