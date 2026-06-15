---
title: Syntax
icon: lucide/braces
---

# Syntax & The Rhombus DSL

Rhombus provides a powerful Domain Specific Language (DSL) embedded directly in Python. Rather than writing verbose JSON by hand, Rhombus lets you express Minecraft density functions and worldgen logic using standard Python mathematical operators. 

Behind the scenes, Rhombus builds an Abstract Syntax Tree (AST) that is then serialized into standard Minecraft worldgen JSON files.

## The `Density` Object

The core of the Rhombus DSL is the `Density` class. Almost every worldgen expression you write or function you call in Rhombus returns a `Density` object. This object acts as a symbolic representation of a density function tree.

### Automatic Type Conversion (`AnyDensity`)

To make writing expressions natural, Rhombus automatically converts common Python types into their corresponding density functions when interacting with a `Density` object:

*   **Numbers (`int` or `float`):** Automatically converted to `minecraft:constant` density functions. Large numbers are automatically split into valid multiplications if they exceed Minecraft's internal constant limits.
*   **Strings (`str`):** Automatically treated as references (`minecraft:reference`) to other density functions, either vanilla or defined elsewhere in your datapack.

For example, writing `Density.refer("minecraft:y") * 2.5` perfectly translates into a `minecraft:mul` function multiplying the `y` reference by a `2.5` constant.

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

```python
# Create a hopper shape and carve out noise from it using the OR operator (Min)
out = hopper | noise(n, xz_scale=1, y_scale=1)
```

### Comparisons and Conditionals

Because `Density` objects are symbolic, you **cannot** use standard comparison operators (`<`, `>`, `<=`, `>=`, `==`) or standard `if / else` blocks to branch worldgen logic based on a density's value. 

Attempting to do so (e.g., `if density > 5:`) will raise a `NotImplementedError`.

Instead, Minecraft provides specific functions for conditional logic. In Rhombus, you should use macros or standard types like `range_choice` to handle conditionality:

```python
# WRONG:
# if y_level > 64: return a else return b

# RIGHT (using Rhombus DSL):
from rhombus.std.types import range_choice

out = range_choice(input=y_level, min_inclusive=64, max_exclusive=10000, when_in_range=a, when_out_of_range=b)
```

*(Note: Rhombus also provides higher-level conditional macros in `rhombus.macros` to make this even easier).*

---

## Defining & Referencing Densities

Sometimes you don't just want to build an inline math expression; you need to store it as a standalone file in your datapack or reference an external one.

Rhombus provides several class methods on the `Density` class for this:

*   **`Density.refer("namespace:id")`**: Creates a reference to an externally defined density function.
*   **`Density.configured("my_pack:my_shape", default=...)`**: Creates a density object that acts as a configurable reference. It defines the `default` density tree, but attaches the identifier `my_pack:my_shape` to it so it can be easily referenced or overridden elsewhere.
*   **`Density.partitioned(value)`**: Wraps a density expression and instructs Rhombus to compile it into a separate, auto-generated JSON file (e.g., `rhombus:partitioned/abc123...`). This is crucial for **caching**, as Minecraft can cache the outputs of density functions that live in their own files, preventing expensive recalculations.