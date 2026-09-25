__all__ = [
    "DensityFunction",
    "SimpleDensityFunction",
    "MappedDensityFunction",
    "DoubleArgumentDensityFunction",
    "Reference",
    "constant",
    "Unknown",
]


from typing import ClassVar, Self
import warnings

from beet.contrib.worldgen import WorldgenDensityFunction

from rhombus.core.node import RhombusASTNode, FieldMeta, field 
from rhombus.core.serializer import deserialize_any_inline, serialize_any_inline
from rhombus.core.utils import JSONDict, JSONValue, BeetFile, annotated_fields
from rhombus.runtime import rho


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
        active_env = rho

        result = {"type": self.id}
        
        rhombus_fields = getattr(self.__class__, "__rhombus_fields__", {})
        
        for parameter, value in self.fields.items():
            if value is None:
                continue
            
            meta: FieldMeta = rhombus_fields.get(parameter)
            json_key = parameter
            if meta:
                if not meta.is_present(active_env):
                    continue
                json_key = meta.get_appropriate_key(active_env, default=parameter)
                if meta.validate:
                    import inspect
                    sig = inspect.signature(meta.validate)
                    if len(sig.parameters) == 1:
                        if not meta.validate(value):
                            warnings.warn(f"Validation failed for field '{parameter}' of '{self.id}'")
                    elif len(sig.parameters) == 2:
                        if not meta.validate(value, self):
                            warnings.warn(f"Validation failed for field '{parameter}' of '{self.id}'")
            result[json_key] = serialize_any_inline(value)
            
        return result

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

                target_class = rho.density_function_type_deserialization_register.get(
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
                    f"Cannot deserialize density function from type '{type(data).__name__}' at top level"
                )

        fields = annotated_fields(cls)
        rhombus_fields = getattr(cls, "__rhombus_fields__", {})
        
        kwargs = {}
        for parameter, tp in fields.items():
            meta: FieldMeta = rhombus_fields.get(parameter)
            json_key = parameter
            if meta:
                json_key = meta.get_appropriate_key(rho, default=parameter)
            
            # Check the expected json_key first
            found_key = None
            if json_key in data:
                found_key = json_key
            else:
                # If not found, try all other possible keys (allows deserializing JSON from any version)
                possible_keys = [parameter]
                if meta and meta.legacy_keys:
                    possible_keys.extend(meta.legacy_keys.values())
                for pk in possible_keys:
                    if pk in data:
                        found_key = pk
                        warnings.warn(
                            f"Expected key '{json_key}' not found in JSON for '{cls.id}'. "
                            f"Falling back to alternative key '{pk}'."
                        )
                        break
            
            if found_key:
                val = deserialize_any_inline(data[found_key], tp)
                if meta and meta.validate and val is not None:
                    import inspect
                    sig = inspect.signature(meta.validate)
                    if len(sig.parameters) == 1:
                        if not meta.validate(val):
                            warnings.warn(f"Validation failed for field '{parameter}' of '{cls.id}'")
                    # 2-arg validators require the node instance which isn't created yet during deserialization
                kwargs[parameter] = val
                
        return cls(**kwargs)

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
                f"Cannot deserialize inline density function from type '{type(data).__name__}'"
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
    density function types that map an argument `input` to a value.
    """

    input: DensityFunction = field(legacy_keys={111.0: "argument"})

    def __repr__(self) -> str:
        return type(self).__name__ + "(" + self.input.__repr__() + ")"
        

class DoubleArgumentDensityFunction(DensityFunction):
    """The **`DoubleArgumentDensityFunction`** base class implements functionality for
    density function types that take two arguments `left` and `right`.
    """

    left: DensityFunction = field(legacy_keys={111.0: "argument1"})
    right: DensityFunction = field(legacy_keys={111.0: "argument2"})

    def __repr__(self) -> str:
        return (
            type(self).__name__
            + "("
            + self.left.__repr__()
            + ", "
            + self.right.__repr__()
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
                f"Cannot initialize Reference object with default of type {type(self.definition).__name__}"
            )

    @property
    def identifier(self) -> str:
        return self.target

    @classmethod
    def deserialize_inline(cls, data: str):
        data = "minecraft:" + data if ":" not in data else data

        dp = rho.datapack
        if dp is not None and (f := dp[WorldgenDensityFunction].get(data)) is not None:
            if rho.deserialize_references_inline:
                return DensityFunction.deserialize_toplevel(f.data)
            return Reference(data, DensityFunction.deserialize_toplevel(f.data))

        return Reference(data)

    # deserialize_toplevel() is not a realistic scenario

    def serialize_toplevel(self) -> JSONDict:
        if self.definition is not None:
            return self.definition.serialize_toplevel()
        import rhombus.support.vanilla.types as vt

        return vt.add(self, constant(0.0)).serialize_toplevel()

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
        elif "generated" in self.identifier:
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
    value: float = field(legacy_keys={111: "argument"})

    @classmethod
    def deserialize_toplevel(cls, data: dict | int | float):
        if isinstance(data, dict):
            return super().deserialize_toplevel(data)
        return cls(float(data))

    def serialize_toplevel(self) -> float | JSONDict:
        import rhombus.support.vanilla.types as vt 

        def ensure_not_exceeding_limit(value: float) -> JSONValue:
            if abs(value) <= vt.literal_number_limit:
                return value

            return vt.mul(
                ensure_not_exceeding_limit(value / vt.literal_number_limit),
                vt.literal_number_limit,
            ).serialize_inline()

        return ensure_not_exceeding_limit(self.value)

    def __repr__(self) -> str:
        return str(self.value)


class Unknown(DensityFunction):
    id: str
    data: JSONDict

    @classmethod
    def deserialize_toplevel(cls, data: JSONDict) -> Self:
        return cls(data["type"], {k: v for k, v in data.items() if k != "type"})

    def serialize_inline(self) -> JSONDict:
        return self.data | {"type": self.id}
