from dataclasses import dataclass, fields
from typing import TypeVar, ClassVar, Callable, Self, TypeAlias
from abc import ABC, abstractmethod
import uuid
from beet import DataModelBase

BeetFileClass = TypeVar("BeetFileClass", bound=DataModelBase)
NEUAdditionalResource: TypeAlias = "AdditionalResourceBase"

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
    def reference_identifier(self) -> str: ...

    @classmethod
    @abstractmethod
    def decode(cls, dict) -> Self: ...

    @abstractmethod
    def encode(self) -> dict: ...


    # - Generierung des Referenzennamen für etwaige Parameter in dem encoded dict
    # - 