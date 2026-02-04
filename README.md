<h1 align="center"><sub><img src="logo.png" height="35"></sub> Rhombus <sub><img src="logo.png" height="35"></sub></h1>
<p align="center">A Python embedded Domain Specific Language for Minecraft Terrain Generation</p>
<p align="center"><code>pip install rhombus</code></p>

### Abstract

Rhombus is a Python sub-language delivered as a package that can be used to create expressions resembling the abstract syntax trees of density functions for Minecraft.<br>
It allows you to comfortably write density functions while benefiting from Python's forgiving syntax.

###### <sub>This project is pretty similar to [misode/gaia-beet](https://github.com/misode/gaia-beet), which you might also find useful. But know that I started developing Rhombus before I knew about it.<br>The similarities in concept are quite frightening though. The biggest difference to Misode's gaia-beet is that Rhombus is not primarily a beet plugin — although integration is possible and recommended — but rather it is to be seen as a coherent, albeit simple language and it will be further developed and improved in exactly this sense.</sub>

> [!note]
> **State of Development**<br>
> Rhombus already has most features I imagined it to have. But it hasn't been put through its paces yet. There also probably is a lot of potential for optimizing it's internal API. 

## Key Advantages
- 📦 **Object-oriented Design**<br>
Full use of Python’s object model for composing, reusing, and structuring density expressions.
- 📝 **Native Comments**<br>
Density logic is written in Python, so comments work naturally without any custom syntax.
- 📖 **Integrated Documentation**<br>
Functions and classes provide detailed docstrings describing behavior, parameters, and usage.
- ⚡ **Efficient Worldgen Performance**<br>
Density expressions are transpiled into as few files as possible, reducing overhead during chunk generation.
- ⚙️ **High Compatability**<br>
As long as the density function definiton format remains unchanged in new version, generated data works across all Minecraft versions. Supporting additional features from mods is straightforward.

## Features
- **Unified Density Type**: 
Represents any computed density value, independent of its underlying implementation.
- **Intuitive AST Construction**:
Density function trees can be built using arithmetic operators, provided interfaces, or custom methods.
- **Complete Vanilla Coverage**:
High-level Python interfaces for all vanilla density function types.
- **Advanced Macros**:
Shortcuts for more complex, commonly needed processes.

## Get started
To use Rhombus efficiently, the following is recommended:
- A basic understanding of how to use Python and Python modules
- A basic understanding of how to use Beet
- A basic understanding of the meaning and use of density functions in datapacks

## What Rombus is not and what we cannot guarantee it will become
- **A Visualizer Tool**:
Currently, all exising density function visualizing tools are based on JavaScript, making it difficult to embed in Rhombus. But by working with Rhombus in combination with [Beet watch](https://mcbeet.dev/getting_started/#building-the-pack) and Misode's [Worldgen Tools Extension](https://marketplace.visualstudio.com/items?itemName=Misodee.worldgen-tools) you can get quite efficient anyway.