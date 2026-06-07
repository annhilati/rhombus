<h1 align="center"><sub><img src="docs/logo.png" height="35"></sub> Rhombus <sub><img src="docs/logo.png" height="35"></sub></h1>
<p align="center">The Python-embedded Domain Specific Language for Minecraft Terrain Generation</p>
<p align="center"><code>pip install git+https://github.com/annhilati/rhombus.git</code></p>

<p align="center">
    <!-- <a href="#"><img alt="Static Badge" src="https://img.shields.io/pypi/v/rhombus?style=for-the-badge&logo=pypi&logoColor=white&labelColor=4c75a9&label=Version&color=161926"></a> -->
    <a href="#"><img alt="Static Badge" src="https://img.shields.io/badge/Python 3.13+-x?style=for-the-badge&logo=python&logoColor=ffffff&labelColor=4c75a9&color=161926"></a>
    <a href="#"><img alt="Static Badge" src="https://img.shields.io/badge/Beet-x?style=for-the-badge&logo=python&logoColor=ffffff&labelColor=b90d38&color=161926"></a>
</p>

### Abstract

Rhombus is a Python sub-language delivered as a package that can be used to create expressions resembling the abstract syntax trees of density functions for Minecraft.<br>
It allows you to comfortably write density functions while benefiting from Python's forgiving syntax.

###### <sub>This project is pretty similar to [misode/gaia-beet](https://github.com/misode/gaia-beet), which you might also find useful. But know that I started developing Rhombus before I knew about it.<br>The similarities in concept are quite frightening though. The biggest difference to Misode's gaia-beet is that Rhombus is not primarily a beet plugin — although integration is possible and recommended — but rather it is to be seen as a coherent, albeit simple language and it will be further developed and improved in exactly this sense.</sub>

> [!note]
> **State of Development**<br>
> Rhombus already has most features I imagined it to have. But it hasn't been put through its paces yet. There also probably is a lot of potential for optimizing it's internal API. 

## Key Advantages
- 📦 **Object-oriented Design**<br>
Full use of Python’s object model for composing, reusing, and structuring density functions.
- 📝 **Native Comments**<br>
Since Python code is in use, comments work naturally without any custom syntax.
- 📖 **Integrated Documentation**<br>
Functions and classes provide detailed docstrings describing behavior, parameters, and usage.
- ⚡ **Efficient Worldgen Performance**<br>
Density expressions are transpiled into as few files as possible, reducing overhead during chunk generation.
- ⚙️ **High Compatability**<br>
As long as the density function definiton format remains unchanged in new version, generated data works across all Minecraft versions.
- 🛠️ **Generous Modding-API**<br>
Classes can be used to derive support for any features from mods.

## Features
- **Unified Density Type**: 
Represents any computed density value, independent of its underlying implementation.
- **Intuitive AST Construction**:
Density function trees can be built using arithmetic operators, provided interfaces, or custom methods.
- **Data Model Base Classes**:
Most funcionality comes from few base classes, so inheriting new classes is very easy.
- **Complete Vanilla Coverage**:
High-level Python interfaces for all vanilla density function types.
- **Advanced Macros**:
Shortcuts for more complex, commonly needed processes.

## What Rombus is not and what we cannot guarantee it will become
- **A Visualizer Tool**:
Currently, all exising density function visualizing tools are based on JavaScript, making it difficult to embed in Rhombus. But by working with Rhombus in combination with [Beet watch](https://mcbeet.dev/getting_started/#building-the-pack) and Misode's [Worldgen Tools Extension](https://marketplace.visualstudio.com/items?itemName=Misodee.worldgen-tools) you can get quite efficient anyway.