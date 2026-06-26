---
title: Syntax
icon: lucide/braces
---

# Syntax & The Rhombus DSL

Rhombus provides a powerful Domain Specific Language (DSL) embedded directly in Python. Rather than writing verbose JSON by hand, Rhombus lets you express Minecraft density functions and worldgen logic using standard Python mathematical operators. 

Behind the scenes, Rhombus builds an Abstract Syntax Tree (AST) that is then serialized into standard Minecraft worldgen JSON files.

## The `Density` Object

The core of the Rhombus DSL is the `Density` class. All worldgen expressions resembling density functions return a `Density` object. This object acts as a symbolic representation of a density function tree.

## Macros

Functions that return `Density` objects we call macros. They can either instaciate the object manually or call other macros. Macros are especially usefull for abstracting away complex, unreadable or unintuitive functions while using other macros. But every implementd density function type has a *builtin*-macro too that directly instanciates the `Density` object and its content which will be a `DensityFunction` subclass instance.

### Automatic Type Conversion & Shorthands

The Macro infrastructure brings the `@macro` decorator and the `AnyDensity` AliasType. To make writing expressions natural, function decorated with `@macro` automatically resolve certain shorthands to `Density` instances:

*   **Numbers (`int` or `float`):** Automatically converted to density functions of type `minecraft:constant`. Large numbers are automatically split into valid multiplications if they exceed Minecraft's internal constant limits.
*   **Strings (`str`):** Automatically treated as references a density function pseudo type. The information yielded by these objects is limited, but they interact seaminglessly with other density functions.

Shorthands will also be converted when using arithmetic operators. 

---

## Operations & Math

Because `Density` objects represent symbolic calculation trees rather than immediate values, you can compose them using standard Python operators.

### Arithmetic Operators

| Python Operator | Example | Minecraft Function |
| :--- | :--- | :--- |
| `+` (Add) | `a + b` | `minecraft:add` |
| `-` (Subtract) | `a - b` | `minecraft:add` (where `b` is multiplied by `-1`) |
| `*` (Multiply) | `a * b` | `minecraft:mul` |
| `/` (Divide) | `a / b` | `minecraft:mul` with `minecraft:invert` on `b` |
| `** 2` (Square) | `a ** 2` | `minecraft:square` |
| `** 3` (Cube) | `a ** 3` | `minecraft:cube` |
| `-` (Negation) | `-a` | `minecraft:mul` (multiplying `a` by `-1`) |
| `abs()` (Absolute)| `abs(a)` | `minecraft:abs` |

*Note: Raising a density to a power higher than 3 (e.g., `a ** 4`) will be unrolled into chained `minecraft:mul` functions.*

### Minimum & Maximum (Bitwise Operators)

In standard Python, `min()` and `max()` evaluate eagerly. Since Rhombus needs to build an AST, it overrides the bitwise AND (`&`) and OR (`|`) operators to represent `minecraft:max` and `minecraft:min` respectively.

*   **`&` (Max):** `a & b` creates a `minecraft:max` function.
*   **`|` (Min):** `a | b` creates a `minecraft:min` function. (Often used for "cutting" or carving shapes).


### Comparisons and Conditionals

Because `Density` objects are symbolic, you **cannot** use standard comparison operators (`<`, `>`, `<=`, `>=`, `==`) or standard `if / else` blocks to branch worldgen logic based on a density's value. 

Attempting to do so (e.g., `if density > 5:`) will raise a `NotImplementedError`.

Instead, Minecraft provides specific functions for conditional logic. In Rhombus, you should use macros or standard types like `range_choice` to handle conditionality. Rhombus also provides higher-level conditional macros in `rhombus.macros.conditional` to make this even easier.

```python
# WRONG:
# if y_level > 64: return a else return b

# RIGHT (using Rhombus DSL):
from rhombus.std.types import range_choice

out = range_choice(input=y_level, min_inclusive=64, max_exclusive=10000, when_in_range=a, when_out_of_range=b)
```

---

## Defining & Referencing Densities

Sometimes you don't just want to build an inline math expression; you need to store it as a standalone file in your datapack or reference an external one.

Rhombus provides several class methods on the `Density` class for this:

*   **`Density.refer("namespace:id")`**: Creates a reference to an externally defined density function.
*   **`Density.configured("my_pack:my_shape", default=...)`**: Creates a density object that acts as a configurable reference. It defines the `default` density tree, but attaches the identifier `my_pack:my_shape` to it so it can be easily referenced or overridden elsewhere.
*   **`Density.partitioned(value)`**: Wraps a density expression and instructs Rhombus to compile it into a separate, auto-generated JSON file (e.g., `rhombus:partitioned/abc123...`). This is crucial for **caching**, as Minecraft can cache the outputs of density functions that live in their own files, preventing expensive recalculations.