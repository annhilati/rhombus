from typing import Any, TypeAlias
from density.core.density import Density, dft

def check_for_references(*args: list[Any]) -> tuple[Any | Density[dft.Reference]]:
    "Takes a list of arguments and gives it back as a tuple, but with all str replaced by a DensityExpression[Reference]"
    out = []
    for arg in args:
        if isinstance(arg, str):
            out.append(Density(dft.Reference(arg)))
            continue
        out.append(arg)
    return tuple(out)

HOLDER_HELPER_CODEC: TypeAlias = dict | str | float
DIRECT_CODEC       : TypeAlias = dict | float