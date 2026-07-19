<a href="#"><img width="2000" alt="Header" src="docs/images/header.svg" /></a>

<h1 align="center">
    <a href="https://annhilati.github.io/rhombus"><img alt="Static Badge" height="38" src="https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/compact-minimal/documentation/ghpages_vector.svg"></a>
    <a href="https://discord.gg/Wwn3TvpMKu"><img alt="Static Badge" height="38" src="https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/compact/social/discord-plural_vector.svg"></a>
    <a href="https://pypi.org/project/rhombus/"><img alt="Static Badge" height="38" src="https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/compact-minimal/available/pypi_vector.svg"></a>
</h1>

<!-- <h1 align="center"><sub><img src="docs/images/logo.svg" height="35"></sub> Rhombus <sub><img src="docs/images/logo.svg" height="35"></sub></h1>
<p align="center">The Python-embedded Domain Specific Language for Minecraft Terrain Generation</p> -->
<p align="center">
    <!-- <a href="#"><img alt="Static Badge" src="https://img.shields.io/pypi/v/rhombus?style=for-the-badge&logo=pypi&logoColor=white&labelColor=4c75a9&label=Version&color=161926"></a> -->
    <a href="#"><img alt="Static Badge" src="https://img.shields.io/badge/Python 3.14+-x?style=for-the-badge&logo=python&logoColor=ffffff&labelColor=4c75a9&color=161926"></a>
    <a href="#"><img alt="Static Badge" src="https://img.shields.io/badge/Beet-x?style=for-the-badge&logo=python&logoColor=ffffff&labelColor=b90d38&color=161926"></a>
    <a href="#"><img alt="Static Badge" src="https://img.shields.io/badge/Deepslate-x?style=for-the-badge&logo=typescript&logoColor=ffffff&labelColor=4b77c3&color=161926"></a>
    <br>
</p>


<p align=right><strong>Terrain development in Minecraft relies on large, deeply nested JSON structures that quickly become difficult to read and maintain. Rhombus introduces powerful abstractions and a comprehensive Python API, making world generation code cleaner, more modular, and significantly faster to develop.</strong></p>

Rhombus is an eDSL delivered as a Python package that allows worldgen developers to comfortably write expressions resembling the abstract syntax trees of density functions for Minecraft while benefiting from Python's forgiving syntax.

<h6><sub>This project is pretty similar to <a href="https://github.com/misode/gaia-beet">misode/gaia-beet</a>, which you might also find useful. Know that I started developing Rhombus before I knew about it, the similarities in concept are quite frightening though. The biggest difference to Misode's gaia-beet is that Rhombus does not see itself as a mere Beet plugin — although we heavily rely on it — but rather as a coherent, mostly separated language and it will be further developed and improved in exactly this sense.</sub></h6>

<!-- > [!note]
> **State of Development**<br>
> Rhombus already has most features I imagined it to have. But it hasn't been put through its paces yet. There also probably is a lot of potential for optimizing it's internal API.  -->

## Key Advantages
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

## Features
<details>
<summary>Unveil</summary>

*This list only includes features that are principially not neccessary, but make up the real strengths of Rhombus.*

- **Rhombus Preview**  
    A lightweight local frontend with file-watching for previewing density functions
  - Visualizer (built on deepslate)
    - Supports all major worldgen mods (see *Mod Support*)
  - File Explorer & Viewer (built on monaco)
  - Spline Visualization
- **Macro Library**
  - [General Math](https://github.com/annhilati/rhombus/blob/main/rhombus/macros/math.py)
    - sum, prod
    - Infinity, NaN
    - round, floor, ceil, mod
    - sgn, heaviside, monus, ramp
  - [Spline approximations](https://github.com/annhilati/rhombus/blob/main/rhombus/macros/smath.py)
    - [Sampler for any Python function](https://github.com/annhilati/rhombus/blob/main/rhombus/splines.py)
    - sin, cos, tan, atan, tanh, coth
    - exp (with arbitrary base)
    - smoothstep, normalPDF, normalCDF, erf, logistic
  - [Performance optimization](https://github.com/annhilati/rhombus/blob/main/rhombus/macros/performance.py)
    - evaluate the number of unique nodes of a function
    - automatically cache specific sub functions of a function
    - automatically cache all recurring sub functions of a function
  - [Expensive iterative Methods](https://github.com/annhilati/rhombus/blob/main/rhombus/macros/emath.py)
    - sqrt
    - sin, cos, tan, exp, ln
    - round, ceil, floor, mod
  - [Working with Maps](https://github.com/annhilati/rhombus/blob/main/rhombus/macros/maps.py)
    - extrude_heightmap
  - [Fluent Interface for conditionality](https://github.com/annhilati/rhombus/blob/main/rhombus/macros/conditional.py)
  - [Coordinate reconstruction](https://github.com/annhilati/rhombus/blob/main/rhombus/macros/coords.py)
- **Mod Support**
  - More Density Functions
  - Lithostitched
  - Tectonic
  - En-sityFunctions
</details>

## Impressions
```sh
pip install rhombus
```

```py
from rhombus import *

continent_noise = Noise(-10, [2, 1, 2, 2, 2, 1, 1, 1, 1])
erosion_noise   = Noise(-9, [3.5, 0, 2, 4, 2, 2, 3])

erosion = clamp(noise(erosion_noise, xz_scale=1.3, y_scale=0) - 0.1, min=-1, max=1)

height_map = spline(erosion, [
    (-1,    -1,     0),
    (-0.6,  -0.95,  0),
    (-0.61, -0.6,   0),
    (-0.2,  -0.55,  0),
    (-0.21, -0.2,   0),
    ( 0.05, -0.2,   0),
    ( 0.21,  0.2,   0),
    ( 0.6,   0.3,   0),
    ( 0.61,  0.8,   0),
    ( 1,     0.8,   0)
])

FINAL = maps.extrude_heightmap(height_map, (-1, 0.8), (64, 256))
```

![Preview](docs/images/preview.png)
