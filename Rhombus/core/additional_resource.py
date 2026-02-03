from dataclasses import dataclass
from typing import ClassVar, Self, Protocol, Callable, Any
from abc import ABC, abstractmethod

from Rhombus.core.utils import uuid_hash

__all__ = ["AdditionalResource", "BeetFileClass"]

class BeetFileClass(Protocol):
    "Protocol for beet file classes."
    encoder: Callable[[dict[str, Any]], str]
    data: dict
    extension: str
    scope: tuple[str, ...]


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
    def decode(cls, dict: dict[str, Any]) -> Self: ...

    @abstractmethod
    def encode(self) -> dict[str, Any]: ...

    @abstractmethod
    def __eq__(self, other) -> bool: ...
    
    def __hash__(self) -> int:
        return hash(uuid_hash(self.encode()))