"""Provides integration and standard definitions for widely used Minecraft world generation mods.

This package serves as a central hub for third-party mod support, 
exposing their custom density functions and node types for native use within Rhombus.

When decoding density functions from datapacks while they are using density functions from
mods or such from old Minecraft versions, make sure to register the respective modules in
the deserialization register:
```
from rhombus import *
register(support.lithostitched)
```
"""

from rhombus.support import (
    tectonic, lithostitched, moredfs, ensity, 
    dptoolkit, vanilla_legacy
)