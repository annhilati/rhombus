---
icon: lucide/lightbulb
title: Introduction
---

Density functions are Minecraft's way to describe, how terrain should look at a certain point.
Starting with 1.18.2, they are data driven, which means that terrain can be modified through a [datapack](https://minecraft.wiki/w/Data_pack), without the need to know how to program in Java. 

However, like many other things in datapacks, writing these is difficult due to the incomprehensible source format and the lack of good development environments.
In addition, the difficulty of density functions goes beyond mere development know-how and also requires a high degree of mathematical background knowledge and creativity — similar to the development of shaders.

*Rhombus* [ˈʁɔmbʊs] is a tool that facilitates some of these aspects, primarily designed to speed up the work process when you already know what you are doing.

!!! info "Beet Interoperability"
    Rhombus is built on the Python-based datapack toolkit [Beet](https://github.com/mcbeet/beet). File handling and the integrated developing tools use it, but you are not required to use the Beet pipeline itself for your projects.

<h2>So ... What are the keywords?</h2>

<h4>Main Advantages</h4>

- 📦 **Object-oriented Design**<br>
Full use of Python’s object model for composing, reusing, and structuring density functions.
- 📝 **Native Comments**<br>
Since Python code is in use, comments work naturally without any custom syntax.
- 📖 **Integrated Documentation**<br>
Functions and classes provide docstrings describing behavior, parameters, and usage.
- ⚡ **Performance Optimization**<br>
Recurring expressions and resource intense operations can be cached automatically.
- 🗄️ **Macro Library**<br>
Growing collection of macros for common patterns and complex operations, reducing boilerplate and improving readability.
- 🔀 **Multi-Version Compilation**<br>
While Rhombus follows an up-to-date-first approach, density functions can be compiled for older versions too. The most optimal implementation for each version is chosen automatically.


<h2>Installation</h2>

Rhombus is available on the Python Package Index. Alternatively, you can install it via `git`:

=== ":simple-python: pip"

    ```sh
    pip install rhombus
    ```
    or
    ```sh
    pip install git+https://github.com/annhilati/rhombus.git
    ```

=== ":simple-uv: uv"

    ```sh
    uv pip install rhombus
    ```
    or
    ```sh
    uv pip install git+https://github.com/annhilati/rhombus.git
    ```