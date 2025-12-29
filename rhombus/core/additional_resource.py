from dataclasses import dataclass, fields
from typing import TypeVar, ClassVar, Callable, Self
from abc import ABC, abstractmethod
from beet import DataModelBase

BeetFileClass = TypeVar("BeetFileClass", bound=DataModelBase)
AdditionalResource = TypeVar("AdditionalResource", bound="AdditionalResourceBase")

class AdditionalResourceBase(ABC):
    "Base class for resources that have to be declared outside of a density function."

    fileclass: ClassVar[type[BeetFileClass]]

    @property
    @abstractmethod
    def reference(self) -> str: ...

    @abstractmethod
    @classmethod
    def decode(cls, dict) -> Self: ...

    @abstractmethod
    def encode(self) -> dict: ...

    def __hash__(self):
        return hash(self.reference)