from typing import ClassVar, Self
import warnings

from beet.contrib.worldgen import WorldgenDensityFunction

from rhombus.core.node import RhombusASTNode
from rhombus.core.serializer import deserialize_any_inline, serialize_any_inline
from rhombus.core.utils import JSONDict, JSONValue, BeetFile, annotated_fields
from rhombus.core.environment import env

__all__ = [
    "DensityFunction",
    "SimpleDensityFunction",
    "MappedDensityFunction",
    "DoubleArgumentDensityFunction",
    "Reference",
    "constant",
    "Unknown",
]


# ======// DensityFunction Base Class //==========================================================//


class DensityFunction(RhombusASTNode):
    """The **`DensityFunction`** base class implements functionality for nodes
    in the abstract syntax tree of Rhombus that also resemble operations in the
    abstract syntax tree of a density function (so called density function types).

    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/devs/abstraction/)
    """

    fileclass: ClassVar[type[BeetFile]] = WorldgenDensityFunction
    id: ClassVar[str]

    # ======// Serialization //===================================================================//

    def serialize_toplevel(self) -> JSONDict:
        return {
            "type": self.id,
            **{
                parameter: serialize_any_inline(value)
                for parameter, value in self.fields.items()
                if value is not None
            },
        }

    # serialize_inline() is inherited from RhombusASTNode

    @classmethod
    def deserialize_toplevel(cls, data: JSONDict | float | int) -> Self:

        if cls is DensityFunction:
            # Standard JSON object with 'type' key
            if isinstance(data, dict):
                type_field: str | None = data.get("type")

                if type_field is None:
                    raise ValueError(
                        "Cannot deserialize density function from dictionary without key 'type'"
                    )
                if ":" not in type_field:
                    type_field = "minecraft:" + type_field

                target_class = env.density_function_type_deserialization_register.get(
                    type_field
                )
                if target_class is None:
                    warnings.warn(
                        f"Could not deserialize density function with type '{type_field}' from dictionary "
                        "because no DensityFunction subclass with that id is defined. "
                        "A 'Unknown' type instance was created instead, containing the raw data."
                    )
                    return Unknown.deserialize_toplevel(data)

                return target_class.deserialize_toplevel(data)

            # Literal constant
            elif isinstance(data, (int, float)):
                return constant(float(data))
            else:
                raise TypeError(
                    f"Cannot deserialize density function from type '{data.__class__.__name__}' at top level"
                )

        fields = annotated_fields(cls)

        return cls(
            **{
                parameter: deserialize_any_inline(value, tp)
                for parameter, value in data.items()
                if parameter in fields
                for tp in (fields[parameter],)
            }
        )

    @classmethod
    def deserialize_inline(cls, data: JSONDict | float | int | str) -> Self:
        # Literal reference
        if isinstance(data, str):
            return Reference.deserialize_inline(data)
        # Constant or dictionary
        elif isinstance(data, (dict, float, int)):
            return cls.deserialize_toplevel(data)
        else:
            raise TypeError(
                f"Cannot deserialize inline density function from type '{data.__class__.__name__}'"
            )


# ======// Utility Base Classes //================================================================//


class SimpleDensityFunction(DensityFunction):
    """The **`SimpleDensityFunction`** base class implements functionality for
    density function types with no arguments.
    """

    @classmethod
    def deserialize_toplevel(cls, data: dict = {}) -> Self:
        return cls()

    def serialize_toplevel(self) -> JSONDict:
        return {"type": self.id}


class MappedDensityFunction(DensityFunction):
    """The **`MappedDensityFunction`** base class implements functionality for
    density function types that map an argument `argument` to a value.
    """

    argument: DensityFunction

    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + self.argument.__repr__() + ")"


class DoubleArgumentDensityFunction(DensityFunction):
    """The **`DoubleArgumentDensityFunction`** base class implements functionality for
    density function types that take two arguments `argument1` and `argument2`.
    """

    argument1: DensityFunction
    argument2: DensityFunction

    def __repr__(self) -> str:
        return (
            self.__class__.__name__
            + "("
            + self.argument1.__repr__()
            + ", "
            + self.argument2.__repr__()
            + ")"
        )


# ======// Primitives //==========================================================================//


class Reference(DensityFunction):
    target: str
    definition: DensityFunction | None = None

    def __post_init__(self):
        if not isinstance(self.target, str) or not self.target:
            raise ValueError("Reference must have a target of type str defined")
        if self.definition is not None and not isinstance(
            self.definition, DensityFunction
        ):
            raise ValueError(
                f"Cannot initialize Reference object with default of type {self.definition.__class__.__name__}"
            )

    @property
    def identifier(self) -> str:
        return self.target

    @classmethod
    def deserialize_inline(cls, data: str):
        data = "minecraft:" + data if ":" not in data else data

        dp = env.datapack
        if dp is not None and (f := dp[WorldgenDensityFunction].get(data)) is not None:
            if env.deserialize_references_directly:
                return DensityFunction.deserialize_toplevel(f.data)
            return Reference(data, DensityFunction.deserialize_toplevel(f.data))

        return Reference(data)

    # deserialize_toplevel() is not a realistic scenario

    def serialize_toplevel(self) -> JSONDict:
        if self.definition is not None:
            return self.definition.serialize_toplevel()
        from rhombus.std.types import types

        return types.add(self, constant(0.0)).serialize_toplevel()

    def serialize_inline(self) -> str:
        return self.target

    @property
    def inscribed_toplevel_nodes(self) -> set[RhombusASTNode]:
        nodes = set()
        if self.definition is not None:
            nodes.add(self)
            nodes |= self.definition.inscribed_toplevel_nodes
        return nodes

    def __repr__(self) -> str:
        if self.definition is None:
            return '"' + self.identifier + '"'
        elif "partitioned" in self.identifier:
            return "Density.partitioned(" + self.definition.__repr__() + ")"
        else:
            return (
                self.identifier.__repr__()
                + "@ Density("
                + self.definition.__repr__()
                + ")"
            )


class constant(DensityFunction):
    id: ClassVar[str] = "minecraft:constant"
    argument: float

    @classmethod
    def deserialize_toplevel(cls, data: dict | int | float):
        if isinstance(data, dict):
            return cls(float(data["argument"]))
        return cls(float(data))

    def serialize_toplevel(self) -> float | JSONDict:
        from rhombus.std.types import types

        def ensure_not_exceeding_limit(value: float) -> JSONValue:

            if abs(value) < types.literal_number_limit:
                return value

            return types.mul(
                ensure_not_exceeding_limit(value / types.literal_number_limit),
                types.literal_number_limit,
            ).serialize_inline()

        return ensure_not_exceeding_limit(self.argument)

    def __repr__(self) -> str:
        return str(self.argument)


class Unknown(DensityFunction):
    id: str
    data: JSONDict

    @classmethod
    def deserialize_toplevel(cls, data: JSONDict) -> Self:
        return cls(data["type"], {k: v for k, v in data.items() if k != "type"})

    def serialize_inline(self) -> JSONDict:
        return self.data | {"type": self.id}
