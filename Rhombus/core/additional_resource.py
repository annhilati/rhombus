from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, Self
from abc import ABC, abstractmethod

from Rhombus.core.utils import uuid_hash, JSONDict, with_datapack_context
from Rhombus.core import config

from beet import DataPack, JsonFile

__all__ = ["AdditionalResource", "BeetFileClass", "decode_additional_resource"]

# class BeetFileClass(Protocol):
#     "Protocol for beet file classes."
#     encoder: Callable[[dict[str, Any]], str]
#     data: dict
#     extension: str
#     scope: tuple[str, ...]

BeetFileClass = JsonFile

@with_datapack_context
def decode_additional_resource[T: AdditionalResource](ref: str, t: type[T], dp: DataPack = ...) -> T:
    ref = "minecraft:" + ref if not ":" in ref else ref
    if dp is None or dp is ...:
        raise Exception(f"Cannot decode additional resource {ref} of type {t.__name__} with no datapack in arguments or context.")
    return t.decode(dp[t.fileclass][ref].data)


@dataclass(frozen=True)
class AdditionalResource(ABC):
    """Abstract base class for resources that have to be declared in a datapack outside of a density function.
    
    When defining new AdditionalResource types ensure the following:
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
    def decode(cls, dict: JSONDict) -> Self: ...

    @abstractmethod
    def encode(self) -> JSONDict: ...

    @abstractmethod
    def __eq__(self, other) -> bool: ...
    
    def __hash__(self) -> int:
        return hash(uuid_hash(self.encode()))