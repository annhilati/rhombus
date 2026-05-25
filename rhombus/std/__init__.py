"""
# The Rhombus standard library
This module contains all the symbols needed to develop vanilla terrain
generation for datapacks, as well as some tools that are generally well-
suited for this purpose.

Typically, when developing terrain generation, you will want to import
everything from this module. Note that some builtin symbols from Python
might be overwritten. To get them back, you can import from `builtins`.

```
from rhombus import *
from builtins import abs as python_abs
```
"""

from rhombus.std.noise import *
from rhombus.std.macros import *
from rhombus.std.density import *
from rhombus.std.functions import *
from rhombus.std.conditional import *
from rhombus.std import functions as f
from rhombus.std import types as t