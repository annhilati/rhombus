---
title: Roadmap
icon: lucide/map
---

<h6>Last updated: 14.06.2026</h6>

# Roadmap

## ✅ Phase 0: Modeling

Phase 0 focusses on implementing all base functionality for constituting abstract syntax trees for density functions.

#### Base classes
- ✅ **RhombuASTNode**: Base class for all nodes of the abstract syntax tree with default recursive methods.
- ✅ **DensityFunction**: Base class for the nodes of the abstract syntax tree.
- ✅ **Datapack resources**: Base class for resources that are provided by a datapack outside of a density function.
- ✅ **Subparameters**: Base class for groups of parameters that do not require a separate file.
- ✅ **AST representation type**: The `Density` class which is used to operate on composed density functions.

#### Content
- ✅ **Vanilla coverage**: Modeling classes for the vanilla density function types and noise.

## 🚧 Phase 1: Content
- 🚧 **Mod support**: Modeling classes for density function types and datapack resources from common used worldgen libraries.
- 🚧 **Macro infrastructure**: Decorators to help with creating macros.
- 🧪 **Spline generation**: Tools for generating spline configurations.
- 🕔 **Field validation**: Warn when values in fields of density functions are invalid.

## 🕔 Phase 2: Optimization

- 🧪 **Performance evaluation**: Debug methods for quantifying performance costs.
- 🚧 **Caching**: Ensure proper caching in complex scenarios.
- 🕔 **AST optimization**: Optimize the abstract syntax tree to cost less performance.