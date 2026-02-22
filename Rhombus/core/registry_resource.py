from dataclasses import dataclass, is_dataclass
from typing import ClassVar, Self, Any
from abc import ABC, abstractmethod

from beet import JsonFile
from Rhombus.core.utils import JSONDict, uuid_hash, fields, annotated_fields


__all__ = ["RegistryResource", "BeetFileClass"]

BeetFileClass = JsonFile

@dataclass(frozen=True)
class RegistryResource(ABC):
    """Abstract base class for resources that have to be declared in a datapack outside of a density function.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/extending/datapack_resources/)
    """

    fileclass: ClassVar[type[BeetFileClass]]
    # reference: ClassVar[str] # Actually a field in subclasses

    @property
    def _fields(self) -> dict[str, Any]:
        return fields(self)

    @property
    def reference_identifier(self) -> str:
        if self.reference is not None:
            return self.reference if ":" in self.reference else "minecraft:" + self.reference
        return f"rhombus:generated/" + uuid_hash(self.encode())

    @classmethod
    def referenced(cls, identifier: str, /) -> Self:
        identifier = "minecraft:" + identifier if not ":" in identifier else identifier
        return cls(reference=identifier)

    @classmethod
    def decode(cls, data: JSONDict) -> Self:
        from Rhombus.core.codec import decode as unidecode
        fields = annotated_fields(cls)

        return cls(**{
            parameter: unidecode(value, tp)
            for parameter, value in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
        })

    def encode(self) -> JSONDict:
        from Rhombus.core.codec import encode as uniencode
        return {
            parameter: uniencode(value)
            for parameter, value in self._fields.items()
            if value is not None
        }

    @abstractmethod
    def __eq__(self, other) -> bool: ...
    
    def __hash__(self) -> int:
        return hash(uuid_hash(self.encode()))