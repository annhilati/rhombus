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
| `--overlay`, `-o`   | string (repeatable) | Key of an overlay in the datapack to override its files with. Use repeatedly to apply multiple overlays. |
| `--extension`, `-e` | string (repeatable) | Python object path of a [Rhombus addon](addons.md) to load. Use repeatedly to load multiple addons. |
| `--no-watch`, `-n`  | flag                | Deactivates file watching. Preview data will not be updated on file changes.       |

#### Examples
Preview the datapack in the current directory:
```
rhombus preview .
```

Including files and visualizers from Lithostitched:
```
rhombus preview . --extension rhombus.lithostitched
```

Include multiple extension: 
```
rhombus preview test_vanilla -e rhombus.lithostitched -e rhombus.tectonic
```

Apply overlays:
```
rhombus preview tectonic-datapack-3.0.25.zip --extension rhombus.tectonic --extension rhombus.lithostitched --overlay overlay.datapack --overlay overlay.1_21_9 
```