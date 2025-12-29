from __future__ import annotations
from dataclasses import dataclass
from rhombus.core.df_types import Reference
from rhombus.language.density import Density
from rhombus.language.functions import _arg_unwrapper

@dataclass
class ConfiguredDensity():
    """
    """

    def __new__(cls, name: str, default: Density | float):
        default = _arg_unwrapper(default)

        return Density(Reference(name, default))