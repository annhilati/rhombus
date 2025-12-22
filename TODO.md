## Density Function Types

- DensityFunctionType classes don't bring fields
  - Need they to? We have functions that wrap them

- Every density function type needs a class and a function. Can we combine them? Or at least make on of them have nearly no logic?

- Are classitems really needed?

- Doing basic arithmetic with the functions still annotates Density types.
  - Overloaded functions are clunky

Handle density data raw without Densiy class; Density only as wrapper?