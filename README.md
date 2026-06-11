<img width="2000" alt="Header" src="https://github.com/user-attachments/assets/8ce4e4f9-847f-4a0f-9afa-2774b228259f" />

<p align="center">
    <!-- <a href="#"><img alt="Static Badge" src="https://img.shields.io/pypi/v/rhombus?style=for-the-badge&logo=pypi&logoColor=white&labelColor=4c75a9&label=Version&color=161926"></a> -->
    <a href="#"><img alt="Static Badge" src="https://img.shields.io/badge/Python 3.13+-x?style=for-the-badge&logo=python&logoColor=ffffff&labelColor=4c75a9&color=161926"></a>
    <a href="#"><img alt="Static Badge" src="https://img.shields.io/badge/Beet-x?style=for-the-badge&logo=python&logoColor=ffffff&labelColor=b90d38&color=161926"></a>
</p>

<!-- <h1 align="center"><sub><img src="docs/logo.png" height="35"></sub> Rhombus <sub><img src="docs/logo.png" height="35"></sub></h1>
<p align="center">The Python-embedded Domain Specific Language for Minecraft Terrain Generation</p> -->
<p align="center"><code>pip install git+https://github.com/annhilati/rhombus.git</code></p>


**Minecraft terrain generation currently requires pure JSON structures, which can grow into large, nested, hard-to-understand trees. Rhombus instead offers flexible abstraction and a comprehensive Python interface that significantly improves readability, project structures, and development speed.**

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
Recurring expressions and resource intense operations are automatically cached.
- 🗄️ **Macro Library**<br>
Growing collection of macros for common patterns and complex operations, reducing boilerplate and improving readability.


## Impressions
```sh
pip install git+https://github.com/annhilati/rhombus.git
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

FINAL_DESTINY = height_map + y_clamped_gradient(from_y=64, to_y=256, from_value=1.001, to_value=-1.001)
```

Don't want to handwrite a 500+ node float manipulation function to get the current coordinate?
```py
from rhombus import *

def radius() -> Density:
    x = coords.x()
    z = coords.z()

    return emath.sqrt(x**2 + z**2, iterations=1)
```

Using a mod?
```py
from rhombus import *
from rhombus.support import moredfs # Or your mod of choice

def radius() -> Density:
    x = moredfs.x()
    y = moredfs.y()

    return moredfs.sqrt(x**2 + y**2)
```
