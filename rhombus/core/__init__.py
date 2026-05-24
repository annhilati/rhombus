"""
# Rhombus core module
Rhombus mainly consists of abstract syntax trees, whose nodes, represented by classes are defined in this module.
The purpose of this module is to provide basic intefaces for such nodes, as they are needed for resembling vanilla features
as well as they are expected for extending support for features from mods and when defining macros.

In addition to a first-order base class, three base classes are defined for different expected serialization scenarios.

`RhombusASTNode`
    Base class for all nodes of the AST structure.

`DensityFunction`
    Base class for density function types. Only the top-level node requires it's own file.

`DatapackResource`
    Base class for resources that have to be provided separately by a datapack. Every node requires it's own file.

`SubParameters`
    Base class for groupings of parameters. No node requires a file.

For informationen on how to implement classes to support features from mods, see the [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/extending/mod_support/).
"""

from rhombus.core.node import *
from rhombus.core.utils import *
from rhombus.core.serializer import *
from rhombus.core.sub_parameters import *
from rhombus.core.density_function import *
from rhombus.core.datapack_resource import *