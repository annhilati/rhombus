from typing import Any
from density.core.expr import DensityExpression, dft

def replace_references(*args: list[Any]) -> tuple[Any | DensityExpression[dft.Reference]]:
    "Takes a list of arguments and gives it back as a tuple, but with all str replaced by a DensityExpression[Reference]"
    out = []
    for arg in args:
        if isinstance(arg, str):
            out.append(DensityExpression(dft.Reference, argument=arg))
            continue
        out.append(arg)
    return tuple(out)