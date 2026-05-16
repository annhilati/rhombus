from typing import Self, Any
from rhombus.core.utils import BeetFile, fields, FROM_CONTEXT
from enum import Enum
import beet

__all__ = ["SerializationContext", "RhombusASTNode"]

class SerializationContext(Enum):
    TOPLEVEL = object()
    INLINE = object()
    
        
class RhombusASTNode:
    
    def serialize(self, ctx: SerializationContext):
        raise NotImplementedError
    
    @classmethod
    def deserialize(cls, data: dict, ctx: SerializationContext, dp: beet.DataPack | None = FROM_CONTEXT) -> Self:
        raise NotImplementedError
    
    @property
    def fields(self) -> dict[str, Any]:
        "Standard implemenation for getting all parameters of the Node paired with their values."
        return fields(self)
    
    def generated_files(self) -> dict[str, BeetFile]:
        "Standard implementation for recursive search for additional files. Returns all files of all entries in `~.fields`."
        # Additionaly and excluding the one with the content of ~.serialize()
        files = {}
        for param, value in self.fields.items():
            if isinstance(value, RhombusASTNode):
                files |= value.generated_files()
        return files