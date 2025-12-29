from dataclasses import dataclass, fields
from typing import TypeVar, ClassVar, Callable, Self
from abc import ABC, abstractmethod
from beet import DataModelBase

BeetFileClass = TypeVar("BeetFileClass", bound=DataModelBase)
AdditionalResource = TypeVar("AdditionalResource", bound="AdditionalResourceBase")

@dataclass(frozen=True)
class AdditionalResourceBase(ABC):
    """Base class for resources that have to be declared outside of a density function.
    
    Adding new Additional Resources
    - make it a dataclass
    - make it frozen
    - make it hashable
    """

    fileclass: ClassVar[type[BeetFileClass]]

    @property
    @abstractmethod
    def reference(self) -> str: ...

    @classmethod
    @abstractmethod
    def decode(cls, dict) -> Self: ...

    @abstractmethod
    def encode(self) -> dict: ...


    # - Generierung des Referenzennamen für etwaige Parameter in dem encoded dict
    # - 