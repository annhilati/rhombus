from dataclasses import dataclass, fields
from typing import TypeVar, ClassVar, Callable, Self
from beet import DataModelBase

BeetFileClass = TypeVar("BeetFileClass", bound=DataModelBase)
AdditionalResource = TypeVar("AdditionalResource", bound="AdditionalResourceBase")

@dataclass(frozen=True)
class AdditionalResourceBase:
    "Base class for resources that have to be declared outside of a density function."

    fileclass:           ClassVar[type[BeetFileClass]]
    encode:              ClassVar[Callable[[Self], dict]]
    decode:              ClassVar[Callable[[type[Self], dict], Self]]
    identifier:          ClassVar[str]
    from_encoded_string: ClassVar[Callable[[type[Self], str], Self]]

    def __hash__(self):
        return hash(self.identifier)