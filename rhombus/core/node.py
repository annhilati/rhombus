from typing import Self, Literal, Any
from rhombus.core.utils import BeetFileClass, fields
from enum import Enum

class SerializationContext(Enum):
    TOPLEVEL = object()
    INLINE = object()
    
        
class Node:
    
    def serialize(self, ctx: SerializationContext):
        raise NotImplementedError
    
    @classmethod
    def deserialize(cls, data: dict, ctx: SerializationContext) -> Self:
        raise NotImplementedError
    
    @property
    def fields(self) -> dict[str, Any]:
        "Standard implemenation for getting all parameters of the Node paired with their values."
        return fields(self)
    
    def generated_files(self) -> dict[str, BeetFileClass]:
        "Standard implementation for recursive search for additional files. Returns all files of all entries in `~.fields`."
        # Additionaly and excluding the one with the content of ~.serialize()
        files = {}
        for param, value in self.fields.items():
            if isinstance(value, Node):
                files |= value.generated_files()
        return files