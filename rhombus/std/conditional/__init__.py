"""
This module provides a fluent interface for realising conditionality by
constructing nested expressions with `range_choice` and `interval_select`.

**IMPORTANT** If the conditionality produces a density function with recurring parts,
they will automatically be cached.

The syntax goes like this:
```
from rhombus.std.conditional import *

out = (
    when(input).equals(1.0)
        .then(10.0)
    .elsewhen(it).equals(2.0)
        .then(20.0)
    .otherwise(0.0)
)
```
"""

from .fluent import *
from .macros import range_choice, interval_select