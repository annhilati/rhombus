from dataclasses import dataclass
from typing import ClassVar, Self
from abc import ABC, abstractmethod

from beet import DataPack, JsonFile
from Rhombus.core.utils import JSONDict, uuid_hash, with_datapack_context, FROM_CONTEXT


__all__ = ["RegistryResource", "BeetFileClass", "decode_RegistryResource_from_DataPack"]

BeetFileClass = JsonFile

@with_datapack_context
def decode_RegistryResource_from_DataPack[T: RegistryResource](id: str, t: type[T], /, dp: DataPack | None = FROM_CONTEXT) -> T:
    id = "minecraft:" + id if not ":" in id else id
    if dp is None:
        return t.as_pure_reference(id)
    return t.decode(dp[t.fileclass][id].data)


@dataclass(frozen=True)
class RegistryResource(ABC):
    """Abstract base class for resources that have to be declared in a datapack outside of a density function.
    
    When defining new RegistryResource types ensure the following:
    - It is a frozen dataclass
    - It is hashable (through sensible implementations of `__hash__` and `__eq__`)
    - A classmethod `decode(cls, dict) -> Self`
    - A method `encode(self) -> dict` that produces a JSON dictionary
    - A property `reference_identifier(self) -> str` that produces a consistent resource identifier.
    """

    fileclass: ClassVar[type[BeetFileClass]]

    @property
    @abstractmethod
    def reference_identifier(self) -> str: ...

    @classmethod
    @abstractmethod
    def as_pure_reference(cls, id: str) -> Self: ...

    @classmethod
    @abstractmethod
    def decode(cls, dict: JSONDict) -> Self: ...

    @abstractmethod
    def encode(self) -> JSONDict: ...

    @abstractmethod
    def __eq__(self, other) -> bool: ...
    
    def __hash__(self) -> int:
        return hash(uuid_hash(self.encode()))