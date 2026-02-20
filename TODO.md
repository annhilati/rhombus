# Missing

# Every Problem

- configuration is random and has to be standardized
- Lithostiched Noise fabrics dont have tooltip

# Design
- What kind of methods are attributes of Density objects?
- How to name arguments in builtins vs macros? Technical or scientific?

# IDEA
- RegistryResources get a wrapper like Density
  - or fabrics


- [x] §1 Decode registry resources dynamically from `DensityFunction` subclasses
  - [x] §1.1 Annotate with concrete registry resource classes instead of `RegistryResource` in `DensityFunction` fields
- [ ] §2 Decode density functions from a `DataPack`
  - [ ] §2.1 Implement a datapack context
- [ ] §3a Warn for potential invalid values in fields of `DensityFunction` subclasses by some sort of generic description
- [ ] §3b Warn for potential invalid values in fields of `RegistryResource` subclasses by some sort of generic description
- [ ] §4 Perform AST simplification on encoding
  - Wrap raw references
  - Merge literal arithmetic
  - Remove canonically false `range_choice`
- [ ] §5 Add support for Unions, Tuples and Optionals for DensityFunction fields
- [x] §6 Don't use factories, that utilize `__new__`