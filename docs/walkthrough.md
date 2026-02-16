---
icon: lucide/footprints
---

> This introduction may be perceived like a screencast

## Installation

Rhombus is an eDSL or *embedded domain specific language*. "Embedded" meaning that it is not a standalone language, but in this case a module for Python.

So we begin by installing rhombus with the pip command.

```sh
pip install rhombus
```

## Composition

In Rhombus, we *compose*[^1] density functions, by using given symbols and object oriented programming.

We start by opening a Python file.

Importing everything from `Rhombus` or importing `Rhombus` itself should be enough to start, but other import patterns are fine too.

An easy example could look like this:

```py
from Rhombus import *

n = Noise(-5, amplitudes=[1.0])
# We're defining a noise as a separate object. All resources, that can be provided in a datapack,
# but cannot be defined inline in a density function have to be declared like this.
# (In vanilla this only regards noises, but support for similar things from mods is given)

final_destiny = noise(n, xz_scale=1, y_scale=0) + y_clamped_gradient(from_value=1.2, to_value=-1.2, from_y=5, to_y=24)
# Additional to functions, various Python operators can be used. Including +, -, *, /, & and |. 
```

An object representing a density function we call *Density*.

## Implementation

To implement a Density into a datapack, [Beet](https://github.com/mcbeet/beet) is highly recommended.

Using Beet we can easily inject a density function into a DataPack object, either in a Beet plugin:

```py
from beet import Context

def plugin(ctx: Context):

    final_destiny.inject(ctx.data, "minecraft:final_destiny")
```

or in a datapack context:

```py
from beet import DataPack

with DataPack(...) as dp:

    final_destiny.inject(dp, "minecraft:final_destiny")
```

When injecting into a datapack (or compiling in any other way) we have to address a name or resource location to the density function by which it will be accessible.

## Note on Performance and Caching

If we composed a density function with multiple Density variables even if we reuse one variable multiple times, in the output we would only find one file. This is because the density function AST is always flattened to include as few references as possible to reduce overhead.

But of course separate files are needed nevertheless to implement caching. Don't worry, this is covered in functions that need it. We can recognize them if they return a type `Density[Reference]` when we wouldn't expect that.



[^1]: We say *compose*, because neither do we define fundamentally new functions in the process nor do we do actual calculations with them.