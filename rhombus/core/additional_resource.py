from dataclasses import dataclass, fields
from typing import TypeVar, ClassVar, Callable, Self
from abc import ABC, abstractmethod
from beet import DataModelBase

BeetFileClass = TypeVar("BeetFileClass", bound=DataModelBase)
AdditionalResource = TypeVar("AdditionalResource", bound="AdditionalResourceBase")

@dataclass(frozen=True)
class AdditionalResourceBase(ABC):
    "Base class for resources that have to be declared outside of a density function."

    fileclass:           ClassVar[type[BeetFileClass]]

    @abstractmethod
    def encode(self) -> dict: ...

    @classmethod
    @abstractmethod
    def decode(cls, data: dict) -> Self: ...

    @property
    @abstractmethod
    def identifier(self) -> str: ...

    @classmethod
    @abstractmethod
    def from_encoded_string(cls, str) -> Self: ... 

    def __hash__(self):
        return hash(self.identifier)