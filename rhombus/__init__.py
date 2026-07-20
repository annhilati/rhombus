"""The Python-embedded Domain specific Language for Minecraft Terrain Generation.

[Documentation](https://annhilati.github.io/rhombus) •
[GitHub](https://github.com/annhilati/rhombus)

It is recomment to import `*` from this module and from other module only
specific symbols to be able to make the most of the DSL experience. Note
that some builtin symbols from Python might be overwritten. To get them
back, you can import from `builtins` like with this idiom:

```
from rhombus import *
from builtins import abs as python_abs
```
"""

from rhombus.std import *
from rhombus.macros import *
from rhombus.support import *
from rhombus import (
    splines,
    preview,
)
from rhombus.core.environment import env

from rhombus import std as _std

env.load_addons(_std)

# Convenience when importing *
from rich import print

def _warn(message, category, filename, lineno, file=None, line=None):
    print(f"\033[38;2;220;150;80mRhombus Warning\n╰─×\033[0m {message}\n")

import warnings as _warnings
_warnings.showwarning = _warn
