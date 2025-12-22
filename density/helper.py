from typing import Any
from density.core.expr import Density, dft

def check_for_references(*args: list[Any]) -> tuple[Any | Density[dft.Reference]]:
    "Takes a list of arguments and gives it back as a tuple, but with all str replaced by a DensityExpression[Reference]"
    out = []
    for arg in args:
        if isinstance(arg, str):
            out.append(Density(dft.Reference(arg)))
            continue
        out.append(arg)
    return tuple(out)