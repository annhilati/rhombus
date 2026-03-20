from dataclasses import dataclass
from typing import Literal
from rhombus.language import DensityDescriptor

@dataclass
class Condition:

    value: float | tuple[float, float]
    relationship: Literal["equals", "greater", "less", "greaterOrEqual", "lessOrEqual", "between", "betweenInclusively", "unequal"]



@dataclass
class IfThen(Condition):
    argument: DensityDescriptor


