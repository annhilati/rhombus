- [x] §1 Decode Datapack Resources dynamically from `DensityFunction` subclasses
  - [x] §1.1 Annotate with concrete Datapack Resource classes instead of `DatapackResource` in `DensityFunction` fields
- [x] §2 Decode density functions from a `DataPack`
  - [x] §2.1 Implement a datapack context
- [ ] §3a Warn for potential invalid values in fields of `DensityFunction` subclasses by some sort of generic description
- [ ] §3b Warn for potential invalid values in fields of `DatapackResource` subclasses by some sort of generic description
- [ ] §4 Perform AST simplification on encoding
  - Wrap raw references
  - Merge literal arithmetic
  - Remove canonically false `range_choice`
- [x] §6 Don't use factories, that utilize `__new__`
- [x] §7 Implement a universal decoding and encoding system that can be used anywhere
  - Perhaps a large configurable function with type specific lambdas?
  - [x] §5 Add support for Unions, Tuples and Optionals for DensityFunction fields
- [x] §8 Unify wizards in a single fabric, dont use on as a decorator and a fabric
- [x] §9 New system for DataPackResources to store references. They shouldn't be a field in the init. (Not make them frozen anymore?)
  - [x] §9.1 Implement the referenced classmethod in the base class (utilize the field util when instanciating?)
  - [x] §9.2 Implement property setting and store reference secretly
  - [x] §10 Implement separation rules for caching functions
  - [ ] §11 Abstract compiler instructions, so that completely new classes can be hooked in




# TODO Features
- This is stupid: Node.inscribed_toplevel_nodes includes Node itself. This seems to make sense, but in a scenario, where I wan't to implement specificially Node - AND its dependencies of course I get it twice. The second time it might even have another, generated name