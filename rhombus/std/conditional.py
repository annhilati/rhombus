from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, SupportsIndex, Sized, overload, Literal
from enum import Enum

from rhombus.core.density_function import DensityFunction
from rhombus.std.types import range_choice
from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro


# Passe das an deinen bereits definierten "infinitesimalen" Wert an.
EPSILON = 1e-7
INFINITY = 1e10

__all__ = ["when", "Relation"]

def _ensure_pair(value: Sized[SupportsIndex]) -> tuple[float, float]:
    if not isinstance(value, tuple) or len(value) != 2:
        raise TypeError("expected tuple with two floats")
    a, b = float(value[0]), float(value[1])
    return (a, b) if a <= b else (b, a)


class Relation(str, Enum):
    EQUALS = "equals"
    NOTEQUAL = "notequal"
    LESS_THAN = "lessthen"
    GREATER_THAN = "greatherthen"
    LESS_OR_EQUAL = "lessorequal"
    GREATER_OR_EQUAL = "greaterorequal"
    BETWEEN = "between"
    OUTSIDE = "outside"

    @classmethod
    def coerce(cls, value: Relation | str) -> Relation:
        if isinstance(value, cls):
            return value

        key = str(value).strip().lower()
        aliases = {
            "less_than": Relation.LESS_THAN,
            "greater_than": Relation.GREATER_THAN,
            "less_or_equal": Relation.LESS_OR_EQUAL,
            "greater_or_equal": Relation.GREATER_OR_EQUAL,
            "not_equal": Relation.NOTEQUAL,
            "neq": Relation.NOTEQUAL,
            "<": Relation.LESS_THAN,
            ">": Relation.GREATER_THAN,
            "<=": Relation.LESS_OR_EQUAL,
            ">=": Relation.GREATER_OR_EQUAL,
            "==": Relation.EQUALS,
            "!=": Relation.NOTEQUAL,
            "in": Relation.BETWEEN,
            "outside": Relation.OUTSIDE,
        }
        key = aliases.get(key, key)
        return cls(key)


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

    def __bool__(self) -> bool:
        raise TypeError("Condition object cannot be used as bool.")
    
    def not_(self) -> Condition:
        return ~self

    def and_(self, other: Condition) -> Condition:
        return self & other

    def or_(self, other: Condition) -> Condition:
        return self | other

    @property
    def default_input(self) -> Any:
        return None

    @property
    def epsilon(self) -> float:
        return EPSILON

    def then(self, value: AnyDensity) -> "Causality":
        """Specifies the value that is returned, if the condition applies.
        
        Continue with `~.elsewhen()` to specify an alternative condition or
        `~.otherwise()` to specify the fallback value and return the `Density` object.
        """
        return Causality(
            cases=[(self, value.AST)],
            default_input=self.default_input,
            epsilon=self.epsilon,
        )

    def compile(self, when_true: DensityFunction, when_false: DensityFunction) -> DensityFunction:
        raise NotImplementedError("No compilation procedure for generic Condition defined. This is a bug")

@dataclass(frozen=True)
class ComparisonCondition(Condition):
    input: DensityFunction
    relation: Relation
    value: float | tuple[float, float]
    epsilon_value: float = EPSILON

    @property
    def default_input(self) -> DensityFunction:
        return self.input

    @property
    def epsilon(self) -> float:
        return self.epsilon_value

    def compile(self, when_true: DensityFunction, when_false: DensityFunction) -> DensityFunction:
        relation = Relation.coerce(self.relation)

        # Primitive case
        if relation == Relation.BETWEEN:
            low, high = _ensure_pair(self.value)
            return range_choice(
                input=self.input,
                min_inclusive=low,
                max_exclusive=high + self.epsilon,
                when_in_range=when_true,
                when_out_of_range=when_false
            )

        # Other
        if relation == Relation.LESS_THAN:
            v = float(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (-INFINITY, v - self.epsilon), self.epsilon,).compile(when_true, when_false)

        if relation == Relation.LESS_OR_EQUAL:
            v = float(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (-INFINITY, v), self.epsilon, ).compile(when_true, when_false)

        if relation == Relation.GREATER_THAN:
            v = float(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (v + self.epsilon, INFINITY), self.epsilon).compile(when_true, when_false)

        if relation == Relation.GREATER_OR_EQUAL:
            v = float(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (v, INFINITY), self.epsilon).compile(when_true, when_false)

        # Derived relations
        if relation == Relation.EQUALS:
            v = float(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (v, v + self.epsilon), self.epsilon).compile(when_true, when_false)

        if relation == Relation.NOTEQUAL:
            v = float(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (v, v + self.epsilon), self.epsilon).compile(when_true=when_false, when_false=when_true)

        if relation == Relation.OUTSIDE:
            low, high = _ensure_pair(self.value)
            return ComparisonCondition(self.input, Relation.BETWEEN, (low, high + self.epsilon), self.epsilon).compile(when_false=when_true, when_true=when_false)

        raise ValueError(f"Unsupported relation: {relation}")


@dataclass(frozen=True)
class AndCondition(Condition):
    left: Condition
    right: Condition

    @property
    def epsilon(self) -> float:
        return self.left.epsilon if self.left is not None else EPSILON

    def compile(self, when_true: DensityFunction, when_false: DensityFunction) -> DensityFunction:
        return self.left.compile(
            self.right.compile(when_true, when_false),
            when_false,
        )


@dataclass(frozen=True)
class OrCondition(Condition):
    left: Condition
    right: Condition

    @property
    def epsilon(self) -> float:
        return self.left.epsilon if self.left is not None else EPSILON

    def compile(self, when_true: DensityFunction, when_false: DensityFunction) -> DensityFunction:
        return self.left.compile(
            when_true,
            self.right.compile(when_true, when_false),
        )


@dataclass(frozen=True)
class NotCondition(Condition):
    inner: Condition

    @property
    def epsilon(self) -> float:
        return self.inner.epsilon

    def compile(self, when_true: DensityFunction, when_false: DensityFunction) -> DensityFunction:
        return self.inner.compile(when_false, when_true)


@dataclass
class Causality:
    cases: list[tuple[Condition, DensityFunction]] = field(default_factory=list)
    default_input: Any = None
    epsilon: float = EPSILON

    @overload
    def elsewhen(self, other_condition: Condition, /) -> PendingCase: ...
    @overload
    def elsewhen(self, relation: Relation, value: float | tuple[float, float], /) -> PendingCase: ...
    @overload
    def elsewhen(self, input: AnyDensity, relation: Relation, value: float | tuple[float, float], /) -> PendingCase: ...
    def elsewhen(self, *args) -> PendingCase:
        """Specifies an alternative condition with an alternative consequence.
        """
        if len(args) == 1:
            condition = args[0]
        elif len(args) == 2:
            if self.default_input is None:
                raise TypeError("elsewhen(relation, value) ist nur möglich, wenn die erste Bedingung ein Input mitliefert.")
            condition = when(self.default_input, args[0], args[1], epsilon=self.epsilon)
        elif len(args) == 3:
            condition = when(args[0], args[1], args[2], epsilon=self.epsilon)
        else:
            raise TypeError("Unexpected number of arguments. Provide one Condition, a Relation and a value or an Density, a Relation and a value")

        return PendingCase(self, condition)

    def otherwise(self, value: AnyDensity) -> Density[range_choice]:
        """Specifies a fallback option for the conditionality if none of the other
        conditions apply. Returns the finished `Density` object.
        """
        result = value.AST
        for condition, branch_value in reversed(self.cases):
            result = condition.compile(branch_value, result)
        return Density(result)


@dataclass
class PendingCase:
    chain: Causality
    condition: Condition

    def then(self, value: AnyDensity) -> Causality:
        """Specifies the valure that will be returned, if the alternative condition
        applies. Continue with `~.elsewhen()` to specify another alternative or
        `~.otherwise()` to specify the fallback value and return the `Density` object.
        """
        self.chain.cases.append((self.condition, value.AST))
        return self.chain


@overload
def when(input: AnyDensity, relation: Literal["<", ">", "<=", ">=", "==", "!="], value: float) -> Condition: ...
@overload
def when(input: AnyDensity, relation: Literal["between", "outside"], value: tuple[float, float]) -> Condition: ...
def when(input: AnyDensity, relation: Relation, value: float | tuple[float, float], /, *, epsilon: float = EPSILON) -> Condition:
    """Opens a new conditionality expression.
    """
    relation = Relation.coerce(relation)
    return ComparisonCondition(input=input.AST, relation=relation, value=value, epsilon_value=epsilon)

Condition.then = macro(Condition.then)
Causality.otherwise = macro(Causality.otherwise)
PendingCase.then = macro(PendingCase.then)
when = macro(when)