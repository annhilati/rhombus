from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, ClassVar
import base64, struct
from beet.contrib.worldgen import WorldgenDensityFunction

from rhombus.core.additional_resource import AdditionalResourceBase
from rhombus.language.density import Density
from rhombus.language.functions import constant

@dataclass(frozen=True, repr=False)
class Configurable(AdditionalResourceBase):
    """
    """
 
    fileclass: ClassVar = WorldgenDensityFunction

    name: str        = field(init=True)
    default: Density = field(init=True)

    def __post_innit__(self):
        ...

    @property    
    def identifier(self) -> str:
        return self.name

    def encode(self) -> dict[str: Any]:
        return self.default.as_dict()
    
    @classmethod
    def decode(cls, data: dict):
        ...

    @classmethod
    def from_encoded_string(cls, string: str):
        ...
    
    def __eq__(self, other: Configurable):
        return self.name == other.name
    
    def __hash__(self):
        return hash(self.name)