---
title: Abstraction
icon: lucide/hexagon
---
<h6>Updated: 27.06.2026</h6>

!!! abstract
    This article explains the levels of abstraction that Rhombus uses for the abstract syntax tree.
    It is especially helpful to read if you plan to significantly extend its functionality, for example,
    by adding support for mods.

# Introduction to Abstraction in Rhombus

Rhombus uses abstract syntax trees (AST for short) to represent density functions. That is natural
because the data-driven definition format for density functions is tree-like too and so are the
objects used in the levelgen Java implementation. A single operation in the tree of a function is
called a node. The purpose of the nodes is to be able recursively produce the desired data in the
target format.

Nodes are instances of dataclasses (the `@dataclass` decorator generally has not be used). On
serialization, they produce a value (in the typical case where JSON is the target format this will be
a dictionary) that includes the values of the children nodes.

Node classes are not the intefaces worldgen developer usually interact with, they are just data structures.

We also make a fundamental distinction
between serializing from the top of a file and serializing somewhere inside a nested AST strcture.
This is because some values that principially have the same meaning look different in different cases
(examples from vanilla include definition vs. referencing of noises, definition vs referencing of
density functions and the spline configuration format inside of a spline value fields vs anywhere else.
We want to be able to use an expressive value anywhere and not let the user have to use distinct objects
in these cases.). 

All nodes derive from a common class:

<h3>RhombusASTNode (<code>rhombus.core.node.RhombusASTNode</code>)</h3>
This class defines the common interface for alle nodes. This includes these:

- `fields()` essentially returns all values of the node instance as a mapping. No matter how
    the node class is implemented, this must include all of the node's effective children nodes,
    as it is required for serialization in subclasses (see below) and a lot of other things.
- `inscribed_toplevel_nodes` (property) returns all nodes that are defined inside of the node
    that require their own file. This can include the node itself, if it requires an own file no
    matter the circumstances.
- `fileclass` (class variable) provides a class that represents a file for the node type in the
    [Beet](https://github.com/mcbeet/beet) pipeline.
- `reference` (property) returns a generic name that can be used as a file name, if the node
    requires one.
- `serialize_toplevel()` returns the target format-friendly representation of the node as it would
  be at the top of a file.
- `serialize_inline()` returns the target format-friendly representation of the node as it would
  be inside of a nested AST structure.
- `deserialize_toplevel` creates a node instance based of the target format representation of the
  node class from the top of a file.
- `deserialize_inline()` creates a node instance based of the target format representation of the
  node class from somewhere in a nested AST structure.
- `__repr__()`
- `__eq__()`

The base class already implements some methods needed for traversal, but they should be
reimplemented when subclassing.

---

Rhombus provides various base classes for nodes with common usecases.

- <h3>DensityFunction (<code>rhombus.core.density_function.DensityFunction</code>)<h3>
  
    - <h5>SimpleDensityFunction (<code>rhombus.core.density_function.SimpleDensityFunction</code>)<h5>
    - <h5>MappedDensityFunction (<code>rhombus.core.density_function.MappedDensityFunction</code>)<h5>
    - <h5>DoubleArgumentDensityFunction (<code>rhombus.core.density_function.DoubleArgumentDensityFunction</code>)<h5>
  
- <h3>DatapackResources (<code>rhombus.core.datapack_resources.DatapackResource</code>)<h3>
- <h3>SubParameters (<code>rhombus.core.sub_parameters.SubParameters</code>)<h3>