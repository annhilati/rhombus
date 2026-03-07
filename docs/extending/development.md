---
title: Roadmap
icon: lucide/map
---

# Roadmap

## 🚧 Phase 0: Modeling

Phase 0 focusses on implementing all base functionality for constituting abstract syntax trees for density functions.

#### Base classes
- 🚧 **AST representation type**: The `Density` class which is used to operate on composed density functions.
- 🚧 **Density function type classes**: Base classes for the nodes of the abstract syntax tree.
- 🚧 **Datapack resources**: Base class for resources that are provided by a datapack outside of a density function.
- 🚧 **Subparameters**: Base class for groups of parameters that get their own type.

#### Content
- 🚧 **Vanilla coverage**: Modeling classes for the vanilla density function types and noise.

## 🧪 Phase 1: Content
- 🚧 **Mod support**: Modeling classes for density function types and datapack resources from common used worldgen libraries.
- 🧪 **Macro infrastructure**: Decorators to help with creating macros.
- 🧪 **Spline generation**: Tools for generating spline configurations.

## 🕔 Phase 2: Optimization

- 🕔 **Caching**: Ensure proper caching in complex scenarios.
- 🕔 **AST optimization**: Optimize the abstract syntax tree to cost less performance.