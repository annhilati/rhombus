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

from rhombus._prelude import *

from rhombus.core.environment import rho

from rhombus.support import vanilla as _vanilla
rho.require({_vanilla: ...})


# Convenience when importing *
from rich import print
from rich.traceback import install as _install
_install(width=120, show_locals=True)


import warnings as _warnings

def _warn(message, category, filename, lineno, file=None, line=None):
    print(f"[bold #dc9650]Rhombus Warning\n╰─×[/] {message}\n")

_warnings.showwarning = _warn
