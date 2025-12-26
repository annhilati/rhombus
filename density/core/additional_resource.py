from dataclasses import dataclass, asdict
from typing import TypeVar, ClassVar, Callable, Self
from beet import DataModelBase

BeetFileClass = TypeVar("BeetFileClass", bound=DataModelBase)

@dataclass
class AdditionalResourceBase:
    "Base class for resources that have to be declared outside of a density function."

    fileclass:     ClassVar[BeetFileClass]
    encode:        ClassVar[Callable[[Self], dict]]
    decode:        ClassVar[Callable[[type[Self], dict], Self]]
    generate_name: ClassVar[Callable[[Self], str]]

    def __hash__(self):
        return hash(self.generate_name())

    def __eq__(self):
        raise NotImplementedError