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
    """Base class for resources that have to be declared outside of a density function.
    
    Adding new Additional Resources
    - make it a dataclass
    - make it frozen
    - make it hashable
    """

    fileclass: ClassVar[type[BeetFileClass]]

    @property
    @abstractmethod
    def reference_identifier(self) -> str: ...
        # Requirements for implementations of this method
        # - formatted as resource location
        # - same encoded value -> same reference identifier

    @classmethod
    @abstractmethod
    def decode(cls, dict) -> Self: ...

    @abstractmethod
    def encode(self) -> dict: ...