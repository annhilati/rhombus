from density.functions import constant
from density.noise import Noise
from density.core.expr import Density
from density import functions

_symbols = [constant, Noise, functions, Density]
_constants = []

__all__ = [obj.__name__ for obj in _symbols].extend(_constants)

# ╭───────────────────────────────────────────────────────────────────────────────╮
# │                                     Config                                    │ 
# ╰───────────────────────────────────────────────────────────────────────────────╯

import warnings as _warnings
def warning(message, category, filename, lineno, file=None, line=None):
    print(
        f"\n\033[38;2;220;150;80mUnnamed Density Warning\n"
        f"╰─×\033[0m {message}\n"
    )

_warnings.showwarning = warning