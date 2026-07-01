---
title: CLI
icon: lucide/terminal
---
# CLI

Rhombus features the `rhombus` CLI command.

## `rhombus preview`

The `preview` subcommand starts the Rhombus Preview service for a datapack in a given path.

#### Usage
```
rhombus preview PATH [FLAGS]
```

#### Parameters

|      |                     | Description                                                                          |
|:----:| :------------------ | :----------------------------------------------------------------------------------- |
| Arg  | `PATH`              | Absolute or relative part of the datapack root                                       |
| Opt  | `--extension`, `e`  | Python object paths of Beet file classes to include in the preview.                  |
| Flag | `--no-update`, `-n` | Deactivates the file wtaching. The preview data will not be updated on file changes. |

#### Examples
Preview the datapack in the current directory:
```
rhombus preview .
```