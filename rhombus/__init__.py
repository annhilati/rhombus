"""A Python embedded DSL for writing Density Functions for Minecraft Datapacks
"""

from rhombus.language import *
from rhombus.toolchain.beet import compile, inject, summon
from rhombus.macros import *

#======// Config //==============================================================================//

import warnings as _warnings
def _warning(message, category, filename, lineno, file=None, line=None):
    print(
        f"\n\033[38;2;220;150;80mUnnamed Density Warning\n"
        f"╰─×\033[0m {message}\n"
    )

_warnings.showwarning = _warning