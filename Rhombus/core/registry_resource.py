from dataclasses import dataclass
from typing import ClassVar, Self, Any
from abc import ABC, abstractmethod

from beet import DataPack, JsonFile
from Rhombus.core.utils import JSONDict, uuid_hash, with_datapack_context, FROM_CONTEXT, fields
from Rhombus.core.codec import encode as uniencode


__all__ = ["RegistryResource", "BeetFileClass", "decode_RegistryResource_from_DataPack"]

BeetFileClass = JsonFile

@with_datapack_context
def decode_RegistryResource_from_DataPack[T: RegistryResource](id: str, t: type[T], /, dp: DataPack | None = FROM_CONTEXT) -> T:
    id = "minecraft:" + id if not ":" in id else id
    if dp is None or dp[t.fileclass].get(id, default=None) is None:
        return t.referenced(id)
    return t.decode(dp[t.fileclass][id].data)


@dataclass(frozen=True)
class RegistryResource(ABC):
    """Abstract base class for resources that have to be declared in a datapack outside of a density function.
    
    When defining new RegistryResource types ensure the following:
        This has to be reworked
    """

    fileclass: ClassVar[type[BeetFileClass]]
    # reference: ClassVar[str] # Actually a fields in subclasses

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
    @abstractmethod
    def decode(cls, dict: JSONDict) -> Self: ...

    def encode(self) -> JSONDict:
        return {
            parameter: uniencode(value)
            for parameter, value in self._fields.items()
            if value is not None
        }

    @abstractmethod
    def __eq__(self, other) -> bool: ...
    
    def __hash__(self) -> int:
        return hash(uuid_hash(self.encode()))