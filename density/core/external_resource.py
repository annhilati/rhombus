from dataclasses import dataclass
from typing import TypeVar, ClassVar, Callable, Self
from beet import DataModelBase

BeetFileClass = TypeVar("BeetFileClass", bound=DataModelBase)

@dataclass
class ExternalResourceBase:
    "Base class for resources that have to be declared outside of a density function."

    fileclass: ClassVar[BeetFileClass]
    as_json:   ClassVar[Callable[[Self], dict]]