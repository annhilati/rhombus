# Missing

# Every Problem

- The language arg helper functions are still a bit lost
- Decoding functions need safety for annotations like Unions
- configuration is random and has to be standardized
- References somehow get decoded twice by from_datapack. There are some other problems too

# Design
- What kind of methods are attributes of Density objects?
- How to name arguments in builtins vs macros? Technical or scientific?

# IDEA
- RegistryResources get a wrapper like Density


- [x] §1 Decode registry resources dynamically from `DensityFunction` subclasses
  - [x] §1.1 Annotate with concrete registry resource classes instead of `RegistryResource` in `DensityFunction` fields
- [ ] §2 Decode density functions from a `DataPack`
- [ ] §3 Warn for potential invalid values in fields of `DensityFunction` subclasses by some sort of generic description