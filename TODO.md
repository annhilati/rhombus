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
- AdditionalResources get a wrapper like Density


- [ ] §1 Annotate with concrete additional resource classes instead of AdditionalResource in DensityFunctionExpression fields
  - [ ] §1.1 Decode additional resources dynamically from DensityFunctionExpression subclasses
- [ ] $2 Decode density functions from a DataPack