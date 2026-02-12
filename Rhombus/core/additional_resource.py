from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, Self, Protocol, Callable, Any
from abc import ABC, abstractmethod

from Rhombus.core.utils import uuid_hash, JSONDict
from Rhombus.core import config

from beet import DataPack, JsonFile

__all__ = ["AdditionalResource", "BeetFileClass"]

# class BeetFileClass(Protocol):
#     "Protocol for beet file classes."
#     encoder: Callable[[dict[str, Any]], str]
#     data: dict
#     extension: str
#     scope: tuple[str, ...]

BeetFileClass = JsonFile

def decode_additional_resource(ref: str, t: type[AdditionalResource], dp: DataPack = None) -> AdditionalResource:

    token = None
    if dp is not None:
        token = config._current_datapack.set(dp)

    try:
        dp = config._current_datapack.get()

        return t.decode(dp[t.fileclass][ref].data)

    finally:
        if token is not None:
            config._current_datapack.reset(token)

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

    # REGISTERED_ADDITIONAL_RESOURCES: ClassVar[dict[str, type[AdditionalResource]]] = {}
    # "Set of all defined classes inheriting from `AdditionalResource`."
      
    # def __init_subclass__(cls, **kwargs):
    #     super().__init_subclass__(**kwargs)
    #     if hasattr(cls, "id"):
    #         AdditionalResource.REGISTERED_ADDITIONAL_RESOURCES[cls.id] = cls

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