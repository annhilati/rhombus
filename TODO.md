## Density Function Types

- Every density function type needs a class and a function. Can we combine them? Or at least make on of them have nearly no logic?
  - No, because one is core, one is library. We need both, especially if poeple want to add new content

- Are classitems really needed?

## Dynamically generated files and references
- How shall noise DFT be transpiled to json, when it is not a reference and files can't be created in the context?
- Shall any declaration of a non-referencing Noise invoke a file creation?

    - We encode the data in the name!


- Is the TypeVar arg annotation in class definitons wrong?