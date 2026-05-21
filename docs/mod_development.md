---
title: Mod Development
icon: lucide/package
---
# Mod Development

Although Rhombus is written in Python and mods for Minecraft are typically written in Java or Kotlin, it can still be used for development through its [command line interface](cli.md).

<!-- TODO: What is the best way to integrate an entire Beet datapack? -->
<!-- To automatically compile Rhombus when building do the following:

=== ":simple-gradle: Gradle"

    Suppose a project structure like this:
    ```tree
    my-mod/
    ├─ build.gradle
    ├─ terrain/
    │  └─ main.py
    └─ src/
       └─ main/
          ├─ java/
          └─ resources/
             └─ data/
                └─ mymod/
                   ├─ worldgen/
                   ├─ dimension/
                   ├─ tags/
                   └─ ...
    ```

    Add an Exec task to your build.gradle:

    ```groovy
    tasks.register("runCommand", Exec) {
        commandLine "cmd", "/c", "rhombus compile rhombus/main.py FINAL_DESTINY --out src/main/resources --id minecraft:final_destiny"
    }

    build.dependsOn(runCommand)
    ``` -->