"""Provides integration and standard definitions for widely used Minecraft world generation mods.

This package serves as a central hub for third-party mod support, 
exposing their custom density functions and node types for native use within Rhombus.

When decoding density functions from datapacks while they are using function types from
mods or such from old Minecraft versions, make sure to load the respective modules in
the environment like in this idiom:
```
from rhombus import *
env.load(support.lithostitched)
```
"""

from rhombus.support import (
    tectonic, lithostitched, moredfs, ensity, 
    vanilla_legacy
)