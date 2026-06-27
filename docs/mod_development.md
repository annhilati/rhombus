---
title: Mod Development
icon: lucide/package
---

# Mod Development

While Rhombus is a Python-based tool and Minecraft mods are typically written in Java or Kotlin, you can seamlessly integrate Rhombus into your mod development workflow using the [Beet](https://mcbeet.dev/) toolchain. By hooking Beet into your build system, you can automatically generate your worldgen data (like density functions) alongside your regular mod compilation.

The most common approach is to add a custom execution task to your build process that triggers the Beet pipeline and outputs directly into your mod's resources directory.

## Setting Up the Project

Suppose you have a standard Fabric, Forge, or NeoForge project structure, and you want to keep your Python-based worldgen scripts isolated in a `terrain/` folder:

```tree
my-mod/
├─ build.gradle
├─ terrain/
│  ├─ beet.yaml
│  ├─ pack/
│  │  ├─ pack.mcmeta
│  │  └─ ...
│  └─ plugin.py
└─ src/
   └─ main/
      ├─ java/
      │  └─ ...
      └─ resources/
         └─ data/
            └─ mymod/
               ├─ worldgen/
               ├─ dimension/
               ├─ tags/
               └─ ...
```

## Configuring the Build System

=== ":simple-gradle: Gradle"

    Add a custom `Exec` task to your `build.gradle` (or `build.gradle.kts`) to run Beet. Hooking this task into `processResources` ensures that your Rhombus-generated JSON files are created before the mod jar is packaged or the game is launched in your development environment.

    ```groovy title="build.gradle"
    // Register a task to run Beet
    tasks.register("generateWorldgen", Exec) {
        group = "build"
        description = "Runs the Beet pipeline to generate worldgen data via Rhombus."
        
        // Define the working directory to keep paths relative to the beet configuration
        workingDir = file("terrain")
        
        // Basic cross-platform execution handling for Beet
        if (System.getProperty("os.name").toLowerCase().contains("windows")) {
            commandLine "cmd", "/c", "beet"
        } else {
            commandLine "beet"
        }
    }

    // Ensure the data is generated before resources are processed into the build
    processResources.dependsOn(generateWorldgen)
    ```

=== ":simple-apachemaven: Maven"

    If your project uses Maven, you can use the `exec-maven-plugin` to run Beet during the `generate-resources` phase. Add the following to the `<plugins>` section of your `pom.xml`:

    ```xml title="pom.xml"
    <plugin>
        <groupId>org.codehaus.mojo</groupId>
        <artifactId>exec-maven-plugin</artifactId>
        <version>3.1.1</version>
        <executions>
            <execution>
                <id>generate-worldgen</id>
                <phase>generate-resources</phase>
                <goals>
                    <goal>exec</goal>
                </goals>
                <configuration>
                    <!-- Define the working directory to keep paths relative to the beet configuration -->
                    <workingDirectory>${project.basedir}/terrain</workingDirectory>
                    <executable>beet</executable>
                    <!-- Note: On Windows, if 'beet' is not recognized directly, you may need to use:
                         <executable>cmd</executable>
                         <arguments>
                             <argument>/c</argument>
                             <argument>beet</argument>
                         </arguments>
                    -->
                </configuration>
            </execution>
        </executions>
    </plugin>
    ```

*Note: Ensure that Python and Beet are installed and available in your system's `PATH`.*

## Configuring the Beet Project

Your `beet.yaml` configuration should be set up to load any base pack data, run your Rhombus script as a Beet plugin, and output the generated files directly into your mod's `src/main/resources` directory.

```yaml title="terrain/beet.yaml"
data_pack:
  load:
    - pack

pipeline:
  - plugin # Refers to plugin.py in the same directory

# Use a valid relative path to point to your mod's resources folder
output: ../src/main/resources
```

The further development of the density function follows the same principles as described in the rest of the documentation.

## Running the Pipeline

In this setup, your Python script (`plugin.py`) acts as a standard Beet plugin. When evaluated by Beet, the script should use Rhombus to define your density functions, noise settings, or macros, and inject them directly into the active Beet datapack context.

Whenever you build your mod (e.g., using `./gradlew build`) or run your client (`./gradlew runClient`), Gradle will automatically execute the `generateWorldgen` task. Beet will run your Python code, collect the generated JSON files, and place them directly into `src/main/resources/data/` where your mod can access them.