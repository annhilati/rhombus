---
title: CLI
icon: lucide/terminal
---
# CLI

Rhombus features the `rhombus` CLI command.

## rhombus preview

The `preview` subcommand starts the Rhombus Preview service for a datapack in a given path.

#### Usage
```
rhombus preview PATH [PARAMS]
```

#### Parameters

| Parameter           |                     | Description                                                                        |
|:------------------- |:-------------------:|:---------------------------------------------------------------------------------- |
| `PATH`              | string              | Absolute or relative path to the datapack root.                                    |
| `--addon`, `-a`     | string (repeatable) | Python object path of a [Rhombus addon](addons.md) to load. Use repeatedly to load multiple addons. |
| `--no-watch`, `-n`  | Flag                | Deactivates file watching. Preview data will not be updated on file changes.       |

#### Examples
Preview the datapack in the current directory:
```
rhombus preview .
```

Including files and visualizers from Lithostitched:
```
rhombus preview . --addons rhombus.lithostitched
```

Include multiple addons: 
```
rhombus preview test_vanilla -a rhombus.lithostitched -a rhombus.tectonic
```