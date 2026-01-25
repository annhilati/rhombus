from dataclasses import dataclass
from typing import ClassVar, Self, Protocol, Callable, Any
from abc import ABC, abstractmethod

__all__ = ["AdditionalResource", "BeetFileClass"]

class BeetFileClass(Protocol):
    "Protocol for beet file classes."
    encoder: Callable[[Any], str]
    data: dict
    extension: str


@dataclass(frozen=True)
class AdditionalResource(ABC):
    """Base class for resources that have to be declared in a datapack outside of a density function.
    
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
    def decode(cls, dict) -> Self: ...

    @abstractmethod
    def encode(self) -> dict: ...

    @abstractmethod
    def __hash__(self) -> int: ...

    @abstractmethod
    def __eq__(self, other) -> bool: ...