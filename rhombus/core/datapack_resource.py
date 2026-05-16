from dataclasses import dataclass, field
from typing import ClassVar, Self

import beet

from rhombus.core.utils import JSONDict, BeetFile, uuid_hash, annotated_fields, contextfunction, FROM_CONTEXT
from rhombus.core.node import RhombusASTNode
from rhombus.core.serializer import deserialize_any, serialize_any
from rhombus import config

__all__ = ["DatapackResource"]


@dataclass
class DatapackResource(RhombusASTNode):
    """Base class for resources that are provided by a datapack outside of a density function.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/extending/mod_support/datapack_resources/)
    """

    fileclass: ClassVar[type[BeetFile]]
    _reference: str | None = field(init=False, default=None)

    #======// Serialization //===================================================================//
    
    @classmethod
    @contextfunction(dp=config.ctx.datapack)
    def deserialize(cls, data: JSONDict | str, inline: bool = True, dp: beet.DataPack | None = FROM_CONTEXT) -> Self:
        
        # We are in the top of a file -> we expect a JSONDict
        if not inline:
            if not isinstance(data, dict):
                raise ValueError(f"Expected a dict, got '{type(data).__name__}'") 
            
            fields = annotated_fields(cls)

            return cls(**{
                parameter: deserialize_any(value, tp)
                for parameter, value in data.items()
                if parameter in fields
                for tp in (fields[parameter],)
            })
            
        # We are somewhere in a file -> we expect a string
        elif inline:
            if not isinstance(data, str):
                raise ValueError(f"Expected a str, got '{type(data).__name__}'")
            
            id = "minecraft:" + data if not ":" in data else data
            if dp is not None and (file := dp[cls.fileclass].get(id)) is not None:
                return cls.deserialize(file.data, inline=False) # We deserialize the found data from top level context
            return cls.referenced(id)
        
        
    def serialize(self, inline: bool = True) -> JSONDict | str:
        
        # We are in the top of a file -> we deliver the serialized fields
        if not inline:
            return {
                parameter: serialize_any(value)
                for parameter, value in self.fields.items()
                if value is not None
            }
        
        # We are somewhere in a file -> we deliver the reference string
        elif inline:
            return self.identifier
        
        
    #======// Dataclasses //=====================================================================//

    @property
    def identifier(self) -> str:
        "The identifier of the datapack resource including the namespace."
        if self._reference is not None:
            return self._reference if ":" in self._reference else "minecraft:" + self._reference
        return f"rhombus:generated/" + uuid_hash(self.serialize(inline=False))

    @identifier.setter
    def identifier(self, value: str | None) -> None:
        if not isinstance(value, str):
            raise TypeError(f"Cannot asign non-str value '{value} to reference identifier'")
        self._reference = value
        
    @classmethod
    @contextfunction(dp=config.ctx.datapack)
    def from_datapack(cls, dp: beet.DataPack, identifier: str) -> Self | None:
        return cls.deserialize(data=identifier, dp=dp) # The deserialization classmethod can do that

    @classmethod
    def referenced(cls, identifier: str, /) -> Self:
        identifier = "minecraft:" + identifier if not ":" in identifier else identifier
        instance = cls(**{param: None for param in annotated_fields(cls)})
        instance.identifier = identifier
        return instance


    #======// Utility //=========================================================================//

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.identifier == other.identifier
    
    def __hash__(self) -> int:
        return hash(uuid_hash(self.serialize()))
    
    def as_dict(self) -> JSONDict:
        return self.serialize(inline=False)