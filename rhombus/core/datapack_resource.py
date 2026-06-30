from typing import ClassVar, Self, Any
from dataclasses import field
import copy

import beet

from rhombus.core.utils import JSONDict, BeetFile, uuid_hash, annotated_fields, contextfunction
from rhombus.core.node import RhombusASTNode
from rhombus.core.serializer import deserialize_any_inline, serialize_any_inline
from rhombus.core.config import env

__all__ = ["DatapackResource"]


class DatapackResource(RhombusASTNode):
    """The **`DatapackResource`** base class implements functionality for nodes
    in the abstract syntax tree of Rhombus that resemble files that are provided
    by a datapack and cannot be defined inside of a density function, but must be
    referenced.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/abstraction/)
    """

    fileclass: ClassVar[type[BeetFile]]
    _identifier: str | None = field(init=False, default=None)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.reference == other.reference
    
    @property
    def is_reference(self) -> bool:
        return all(v is None for f, v in self.fields.items() if f != "_identifier") and self._identifier is not None
    
    def __copy__(self) -> Self:
        if self.is_reference:
            return self.refer(self._identifier)
        return self.__class__(**self.fields)
    
    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        if self._identifier is not None:
            return self.refer(self._identifier)
        new_fields = {
            name: copy.deepcopy(value, memo)
            for name, value in self.fields.items()
        }
        return self.__class__(**new_fields)


    def __repr__(self) -> str:
        if self.is_reference and self._identifier is not None:
            return '"' + self.reference + '"'
        return super().__repr__()
    
    def __hash__(self):
        # We need to explicitely set it here again, because defining __eq__ sets __hash__ to None
        return super().__hash__()


    #======// Serialization //===================================================================//
    
    @property
    def inscribed_toplevel_nodes(self) -> set[RhombusASTNode]:
        nodes = set()
        if not all(v is None for f, v in self.fields.items() if f != "_identifier"):
            nodes.add(self)
            for param, value in self.fields.items():
                if isinstance(value, RhombusASTNode):
                    nodes |= value.inscribed_toplevel_nodes
        return nodes
    
    @property
    def reference(self):
        if self._identifier is not None:
            return self._identifier if ":" in self._identifier else "minecraft:" + self._identifier
        return f"rhombus:generated/" + uuid_hash(self.serialize_toplevel())
        
    def serialize_toplevel(self) -> JSONDict:
        return {
            parameter: serialize_any_inline(value)
            for parameter, value
            in self.fields.items()
            if value is not None
        }
        
    def serialize_inline(self) -> str:
        return self.reference
    
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
        dp = env.datapack
        if dp is not None and (file := dp[cls.fileclass].get(id)) is not None:
            return cls.deserialize_toplevel(file.data)
        return cls.refer(id)
    
    #======// Workflow //========================================================================//

    @classmethod
    def from_dict(cls, data: JSONDict) -> Self:
        """Creates an instance of this datapack resource node class from a dictionary."""
        return cls.deserialize_toplevel(data)

    @classmethod
    @contextfunction(dp="datapack")
    def from_datapack(cls, dp: beet.DataPack, identifier: str) -> Self | None:
        """Extracts an instance of this datapack resource node class from a Beet datapack."""
        
        identifier = "minecraft:" + identifier if not ":" in identifier else identifier

        file = dp[cls.fileclass][identifier]
        if file is None:
            return None
        
        instance = cls.from_dict(file.data)
        instance.reference = identifier
        return instance

    @classmethod
    def refer(cls, identifier: str, /) -> Self:
        """Creates an instance of this datapack resource node class that
        references an externally provided resource.
        """
        identifier = "minecraft:" + identifier if not ":" in identifier else identifier
        instance = cls(**{param: None for param in annotated_fields(cls)})
        object.__setattr__(instance, "_identifier", identifier)
        return instance
    
    @reference.setter
    def reference(self, value: str | None) -> None:
        if not isinstance(value, str):
            raise TypeError(f"Cannot assign non-string value '{value}' to reference identifier")
        object.__setattr__(self, "_identifier", value)
        
    def as_dict(self) -> JSONDict:
        "Returns the resource as a serialized dictionary, like it would be found in a resource definition file."
        return self.serialize_toplevel()
