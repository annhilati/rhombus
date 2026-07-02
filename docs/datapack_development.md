---
title: Datapack Development
icon: lucide/package
---
# Datapack Developmen

When using Rhombus with datapacks, your project should use the [Beet](https://github.com/mcbeet/beet) pipeline.

In most cases, you will want to integrate a density function defined with Rhombus into a Datapack. To do this, use a Beet plugin and add it to your pipeline. It could look like this:

```python title="compiler.py"
from beet import Context
from rhombus import *

def compile_densities(ctx: Context):

    from .terrain import final_destiny

    final_destiny.implement(ctx.data, "minecraft:overworld/final_destiny")
```
``` yaml title="beet.yml"
load:
    ...
pipeline:
    - compiler.compile_densities
...
```

## Debugging

Rhombus itself does not have great debugging and visualization options. But when using VSCode development can become quite responsive.
To investigate how a change affects a density function, do the following:

1. Install the [Worldgen Tools for Minecraft](https://marketplace.visualstudio.com/items?itemName=Misodee.worldgen-tools) VSCode extension.
2. Start a Beet Watch session and wait for the initial build process to complete.
    ```sh
    beet watch
    ```
3. Open the generated JSON file in the output datapack and select “Open visualizer in current file” from the command palette.
   ![](https://github.com/misode/worldgen-tools/raw/HEAD/images/density_visualizer.png)

Once opened, the visualization will automatically update whenever a new build is triggered by file changes.