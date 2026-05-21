---
icon: lucide/lightbulb
title: Introduction
---

Density function are Minecraft's way to describe, how terrain should look at a certain point.
Starting with 1.18.2, they are data driven, which means that terrain can be modified through a [datapack](https://minecraft.wiki/w/Data_pack), without the need to know how to program in Java. 

However, like many other things in datapacks, writing these is difficult due to the incomprehensible source format and the lack of good development environments.
In addition, the difficulty of density functions goes beyond mere development know-how and also requires a high degree of mathematical background knowledge and creativity — similar to the development of shaders.

*Rhombus* [ˈʁɔmbʊs] is a tool that facilitates some of these aspects, primarily designed to speed up the work process when you already know what you are doing.

!!! info "Beet Interoperability"
    If you already worked with development environments for datapacks, you might be pleased to hear that Rhombus is working hand in hand with the [Beet](https://github.com/mcbeet/beet) pipeline.
    Rhombus can be used without it, but the features that provide a real speed advantage are based on it.

<h2>So ... What are the keywords?</h2>

<h4>Main Advantages</h4>

- 📦 **Object-oriented Design**<br>
Full use of Python’s object model for composing, reusing, and structuring density functions.
- 📝 **Native Comments**<br>
Since Python code is in use, comments work naturally without any custom syntax.
- 📖 **Integrated Documentation**<br>
Functions and classes provide detailed docstrings describing behavior, parameters, and usage.
- 🗄️ **Macro Library**<br>
Collection of macros simplifies various common applications.
- ⚡ **Efficient Worldgen Performance**<br>
Density expressions are transpiled into as few files as possible, reducing overhead during chunk generation.

<h4>Quality Assurance</h4>

- 🛠️ **Generous Modding-API**<br>
Classes can be used to derive support for any features from mods.
- ⚙️ **High Stability**<br>
As long as the format of the density function definition remains unchanged in new versions, the generated data will work in all versions of Minecraft.

<h2>Installation</h2>

Rhombus is currently not available on the Python Package Index. Until that changes, install it via `git`:

=== ":simple-python: pip"

    ```sh
    pip install git+https://github.com/annhilati/rhombus.git
    ```

=== ":simple-uv: uv"

    ```sh
    uv pip install git+https://github.com/annhilati/rhombus.git
    ```

!!! warning
    Please note that with this method, each installation could result in a new version with breaking changes.