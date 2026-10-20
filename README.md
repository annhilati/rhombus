<a href="#"><img width="2000" src="https://raw.githubusercontent.com/annhilati/rhombus/main/docs/images/header.svg" alt="Header"/></a>

<h1 align="center">
    <a href="https://annhilati.github.io/rhombus"><img alt="Static Badge" height="38" src="https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/compact-minimal/documentation/ghpages_vector.svg"></a>
    <a href="https://discord.gg/Wwn3TvpMKu"><img alt="Static Badge" height="38" src="https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/compact/social/discord-plural_vector.svg"></a>
    <a href="https://pypi.org/project/rhombus/"><img alt="Static Badge" height="38" src="https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/compact-minimal/available/pypi_vector.svg"></a>
</h1>

<!-- <h1 align="center"><sub><img src="docs/images/logo.svg" height="35"></sub> Rhombus <sub><img src="docs/images/logo.svg" height="35"></sub></h1>
<p align="center">The Python-embedded Domain Specific Language for Minecraft Terrain Generation</p> -->
<p align="center">
    <a href="#"><img alt="Static Badge" src="https://img.shields.io/badge/Python 3.13+-x?style=for-the-badge&logo=python&logoColor=ffffff&labelColor=4c75a9&color=161926"></a>
    <a href="#"><img alt="Static Badge" src="https://img.shields.io/badge/Beet-x?style=for-the-badge&logo=python&logoColor=ffffff&labelColor=b90d38&color=161926"></a>
    <a href="#"><img alt="Static Badge" src="https://img.shields.io/badge/Deepslate-x?style=for-the-badge&logo=typescript&logoColor=ffffff&labelColor=4b77c3&color=161926"></a>
    <br>
</p>


<p align=right><strong>Terrain development in Minecraft relies on large, deeply nested JSON structures that quickly become difficult to read and maintain. Rhombus introduces powerful abstractions and a comprehensive Python API, making world generation code cleaner, more modular, and significantly faster to develop.</strong></p>

Rhombus is an eDSL delivered as a Python package that allows worldgen developers to comfortably write expressions resembling the abstract syntax trees of density functions for Minecraft while benefiting from Python's forgiving syntax.


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
- 🔀 **Multi-Version Compilation**<br>
While Rhombus follows an up-to-date-first approach, density functions can be compiled for older versions too. The most optimal implementation for each version is chosen automatically.

## Features
<details>
<summary>Unveil</summary>

*This list only includes features that are principally not necessary, but make up the real strengths of Rhombus.*

- **Macro Library**
  - Adaptation of all density function types and noise features in recent versions
  - Caching optimizer
  - General Math
    - Implementations of core functions for older versions: sign, rounding, modulo, etc.
    - Smooth max and min functions
    - Infinity, NaN
    - Sign, Heaviside, ramp and smoothstep functions
    - Spline and exponentiation-based trigonometric functions
    - Spline approximations for some distribution functions: normalPDF, normalCDF, erf, logistic
    - Spline point sampler for arbitrary Python functions
  - Working with Maps
    - Heightmap extrusion
  - Expressive construction of conditionalities
    - Use of the `if / elif / else` keywords in condition blocks and the ternary operator 
    - Fluent Interface
  - Coordinate reconstruction for older versions
- **Mod Support**
  - More Density Functions
  - Lithostitched
  - Tectonic
  - En-sityFunctions
- **Rhombus Preview**  
    A lightweight local frontend with file-watching for previewing density functions
  - Visualizer (built on deepslate)
    - Supports all major worldgen mods (see *Mod Support*)
  - File Explorer & Viewer (built on monaco)
  - Spline Visualization
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
```py
import beet
import beet.contrib.worldgen
import rhombus

from .previous_code_block import FINAL

def beet_default(ctx: beet.Context):

    FINAL.implement(ctx.data, "minecraft:final_destiny")

    print(FINAL.compile("minecraft:final_destiny"))
```

<details>
<summary>Have a look at the results</summary>

```py
{
    (
        'minecraft:final_destiny', WorldgenDensityFunction({
            'type': 'minecraft:sub',
            'left': {
                'type': 'minecraft:add',
                'left': {
                    'type': 'minecraft:mul',
                    'left': {
                        'type': 'minecraft:sub',
                        'left': {
                            'type': 'minecraft:spline',
                            'spline': {
                                'coordinate': {
                                    'type': 'minecraft:clamp',
                                    'input': {
                                        'type': 'minecraft:sub',
                                        'left': {
                                            'type': 'minecraft:noise',
                                            'noise': 'rhombus:generated/dark_drowned_7849',
                                            'shift_x': 0.0,
                                            'shift_y': 0.0,
                                            'shift_z': 0.0,
                                            'xz_scale': 1.3, 
                                            'y_scale': 0
                                        },
                                        'right': 0.1
                                    },
                                    'max': 1.0,
                                    'min': -1.0
                                },
                                'points': [
                                    {'derivative': 0, 'location': -1,    'value': -1.0 },
                                    {'derivative': 0, 'location': -0.6,  'value': -0.95},
                                    {'derivative': 0, 'location': -0.61, 'value': -0.6 },
                                    {'derivative': 0, 'location': -0.2,  'value': -0.55},
                                    {'derivative': 0, 'location': -0.21, 'value': -0.2 },
                                    {'derivative': 0, 'location':  0.05, 'value': -0.2 },
                                    {'derivative': 0, 'location':  0.21, 'value':  0.2 }, 
                                    {'derivative': 0, 'location':  0.6,  'value':  0.3 },
                                    {'derivative': 0, 'location':  0.61, 'value':  0.8 },
                                    {'derivative': 0, 'location':  1,    'value':  0.8 }
                                ]
                            }
                        },
                        'right': -1.0
                    },
                    'right': 106.66666666666666
                },
                'right': 64.0
            },
            'right': {
                'type': 'minecraft:cache',
                'input': {
                    'type': 'minecraft:gradient',
                    'axis': 'y',
                    'from_coordinate': -30000000,
                    'from_value': -30000000,
                    'tiling': 'clamp_to_edge',
                    'to_coordinate': 30000000,
                    'to_value': 30000000
                }
            }
        })
    ),
    (
        'rhombus:generated/dark_drowned_7849', WorldgenNoise({
            'base_octave': -9,
            'base_amplitude': 1.0,
            'normalize': True,
            'octave_count': 7,
            'amplitude_modifiers': (3.5, 0, 2, 4, 2, 2, 3)
        })
    )
}
```
</details>

<h2></h2>

![Preview](https://raw.githubusercontent.com/annhilati/rhombus/main/docs/images/preview.png)

## Spread the Word

The easiest way to support the Rhombus project is to propagate its use in your projects. You can use our custom [Devin's Badges](https://github.com/intergrav/devins-badges):

<p align=center>
  <a href="https://github.com/annhilati/rhombus"><img src="https://raw.githubusercontent.com/annhilati/rhombus/main/docs/images/badge-cozy.svg"/></a>
  <br>
  <code>&lt;a href="https://github.com/annhilati/rhombus">&lt;img src="https://raw.githubusercontent.com/annhilati/rhombus/main/docs/images/badge-cozy.svg"/>&lt;/a></code>
  <br>
  <br>
  <a href="https://github.com/annhilati/rhombus"><img src="https://raw.githubusercontent.com/annhilati/rhombus/main/docs/images/badge-cozy-minimal.svg"/></a>
  <br>
  <code>&lt;a href="https://github.com/annhilati/rhombus">&lt;img src="https://raw.githubusercontent.com/annhilati/rhombus/main/docs/images/badge-cozy-minimal.svg"/>&lt;/a></code>
</p>

<!-- ## Acknowledgements

<details>
<summary>Show</summary>

- gegy – for their improvements of the worldgen system which they consulted the community for
- abkwreu – for inspiring me how to implement syntactic conditionality
- AtronixMH48 – for testing out Rhombus in it's early stages

**For their work in the field**
- Klinbee
- Uni
- Apollo
- Wektory

</details> -->