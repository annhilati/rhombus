from dataclasses import dataclass, asdict
from typing import TypeVar, ClassVar, Callable, Self
from beet import DataModelBase

BeetFileClass = TypeVar("BeetFileClass", bound=DataModelBase)

@dataclass
class ExternalResourceBase:
    "Base class for resources that have to be declared outside of a density function."

    fileclass: ClassVar[BeetFileClass]
    encode:    ClassVar[Callable[[Self], dict]]
    decode:    ClassVar[Callable[[type[Self], dict], Self]]

    def __hash__(self):
        return sum([hash(parameter) for parameter in asdict(self).values()])