from density.language.functions import constant
from density.language.noise import Noise, NoiseReference
from density.language import Density, DensityReference

_symbols = [constant, Noise, NoiseReference, Density]
_constants = []

__all__ = [obj.__name__ for obj in _symbols].extend(_constants)

#======// Config //==============================================================================//

import warnings as _warnings
def warning(message, category, filename, lineno, file=None, line=None):
    print(
        f"\n\033[38;2;220;150;80mUnnamed Density Warning\n"
        f"╰─×\033[0m {message}\n"
    )

_warnings.showwarning = warning