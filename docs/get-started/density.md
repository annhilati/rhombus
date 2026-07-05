---
title: The Density Object
icon: lucide/diamond
---
<h6>Last updated: 30.06.2026</h6>

# The Density Object

Rhombus introduces the `Density` class as the main interface for writing density functions. It is
the type, worldgen developers will deal with most the time.

## Object Creation

```py
from rhombus import Density

df = Density(10)                          # constant number
df = Density("minecraft:continentalness") # referencing another function
```

By default, file names are not chosen but generated. To allow users to configure your datapack or let
other datapacks hook into your datapack, you can set a fixed name for a density function through
the following idiom:
```py
df = "minecraft:my_variable" @ Density(5)
```

#### From Dictionary

```py
from rhombus import Density

df = Density.from_dict({
    "type": "minecraft:mul",
    "argument1": 2,
    "argument2": "minecraft:continentalness"
})
```

#### From Datapack

```py
from rhombus import Density
from beet import DataPack

dp = DataPack(path="pack")

df = Density.from_datapack(dp, "minecraft:overworld/sloped_cheese")
```

!!! info "Context Awareness"

    Deserialization always tries to resolve references from the current datapack. So if a `from_datapack()` call
    targets a density function that somewhere in it references another one, the returned `Density` object will
    contain both completely in its abstract syntax tree.


## Operators

| Python Operator | Minecraft Equivalent                              |
| :-------------- | :------------------------------------------------ |
| `+`             | `minecraft:add`                                   |
| `-`             | `minecraft:add` with `minecraft:mul` with `-1`    |
| `*`             | `minecraft:mul`                                   |
| `**`            | `minecraft:square`, `minecraft:cube`, or chained `minecraft:mul` respectively |
| `/`             | `minecraft:mul` with `minecraft:invert`           |
| `//`            |                                                   |
| `%`            |                                                    |
| `-` (negation)  | `minecraft:mul` with `-1`                         |
| `&`             | `minecraft:max`                                   |
| `|`             | `minecraft:min`                                   |

In-Place operators like `+=`, `*=`, etc. are supported too.


## Source Generation

#### Dictionary

```py
from rhombus import Density

df = Density(10) / 2

df.as_dict()
```
```py
{
  'type': 'minecraft:mul',
   'argument1': 10,
   'argument2': 0.5
}
```

Note that the returned dictionary will contain reference strings if the `Density` had any, but not
their definitions. You will therefore lose information if you just use this method.

#### Files

```py
from rhombus import Density

df = Density(10) / 2

df.compile("main")
```
```py
[
    (
        'minecraft:main', # the 'minecraft' namespace was added automatically
        WorldgenDensityFunction({
            'type': 'minecraft:mul',
            'argument1': 10,
            'argument2': 0.5
        })
    )
]
```

#### Datapack

```py
from rhombus import Density
from beet import DataPack

dp = DataPack(path="pack")

df = Density(10) / 2

df.implement(dp, "main")
```

Or analogue in a Beet plugin:

```py
from rhombus import Density
from beet import Context

df = Density(10) / 2

def beet_default(ctx: Context):
    df.implement(ctx.data, "main")
```