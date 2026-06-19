from typing import ClassVar, Self, Any
from dataclasses import field
import copy

import beet
import beet.contrib.worldgen as worldgen

from rhombus.core.utils import JSONDict, BeetFile, uuid_hash, annotated_fields, contextfunction
from rhombus.core.node import RhombusASTNode
from rhombus.core.serializer import deserialize_any_inline, serialize_any_inline
from rhombus import config

__all__ = ["DatapackResource"]


class DatapackResource(RhombusASTNode):
    """Base class for resources that are provided by a datapack outside of a density function.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/extending/mod_support/datapack_resources/)
    """

    fileclass: ClassVar[type[BeetFile]]
    _reference: str | None = field(init=False, default=None)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.identifier == other.identifier
    
    @property
    def is_reference(self) -> bool:
        return all(v is None for f, v in self.fields.items() if f != "_reference") and self._reference is not None
    
    def __copy__(self) -> Self:
        if self.is_reference:
            return self.refer(self._reference)
        return self.__class__(**self.fields)
    
    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        if self._reference is not None:
            return self.refer(self._reference)
        new_fields = {
            name: copy.deepcopy(value, memo)
            for name, value in self.fields.items()
        }
        return self.__class__(**new_fields)


    def __repr__(self) -> str:
        if self.is_reference and self._reference is not None:
            return '"' + self.identifier + '"'
        return super().__repr__()
    
    def __hash__(self):
        # We need to explicitely set it here again, because defining __eq__ sets __hash__ to None
        return super().__hash__()

    #======// Serialization //===================================================================//
    
    def serialize_toplevel(self) -> JSONDict:
        return {
            parameter: serialize_any_inline(value)
            for parameter, value
            in self.fields.items()
            if value is not None
        }
        
    def serialize_inline(self) -> str:
        return self.identifier
    
    @classmethod
    def deserialize_toplevel(cls, data: JSONDict):
        fields = annotated_fields(cls)

        return cls(**{
            parameter: deserialize_any_inline(value, tp)
            for parameter, value
            in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
        })
        
    @classmethod
    def deserialize_inline(cls, data: str):
        id = "minecraft:" + data if not ":" in data else data
        dp = config.ctx.datapack.get()
        if dp is not None and (file := dp[cls.fileclass].get(id)) is not None:
            return cls.deserialize_toplevel(file.data)
        return cls.refer(id)
    
    @property
    def inscribed_toplevel_nodes(self) -> set[RhombusASTNode]:
        nodes = set()
        if not all(v is None for f, v in self.fields.items() if f != "_reference") and self._reference is None:
            nodes.add(self)
        
            for param, value in self.fields.items():
                if isinstance(value, RhombusASTNode):
                    nodes |= value.inscribed_toplevel_nodes
        return nodes
    
    @property
    def identifier(self) -> str:
        "The identifier of the datapack resource including the namespace."
        if self._reference is not None:
            return self._reference if ":" in self._reference else "minecraft:" + self._reference
        return f"rhombus:generated/" + uuid_hash(self.serialize_toplevel())
    
    @property
    def reference(self):
        return self.identifier
        
    #======// Workflow //========================================================================//

    @classmethod
    def from_dict(cls, data: JSONDict) -> Self:
        return cls.deserialize_toplevel(data)

    @classmethod
    @contextfunction(dp=config.ctx.datapack)
    def from_datapack(cls, dp: beet.DataPack, identifier: str) -> Self | None:
        "Extracts a resource from a Beet datapack."
        
        identifier = "minecraft:" + identifier if not ":" in identifier else identifier

        file = dp[worldgen.WorldgenDensityFunction][identifier]
        if file is None:
            return None
        
        return cls.from_dict(file.data)

    @classmethod
    def refer(cls, identifier: str, /) -> Self:
        "Creates a reference to an externally provided resource."
        identifier = "minecraft:" + identifier if not ":" in identifier else identifier
        instance = cls(**{param: None for param in annotated_fields(cls)})
        object.__setattr__(instance, "_reference", identifier)
        return instance
    
    @identifier.setter
    def identifier(self, value: str | None) -> None:
        if not isinstance(value, str):
            raise TypeError(f"Cannot assign non-string value '{value}' to reference identifier")
        object.__setattr__(self, "_reference", value)
        
    def as_dict(self) -> JSONDict:
        "Returns the resource as a serialized dictionary, like it would be found in a resource definition file."
        return self.serialize_toplevel()
