<h1 align="center"><sub><img src="logo.png" height="35"></sub> Rhombus <sub><img src="logo.png" height="35"></sub></h1>
<p align="center">A Python embedded Domain Specific Language for Minecraft Terrain Generation</p>
<p align="center"><code>pip install rhombus</code></p>

### Abstract

Rhombus is a sub language for Python, delivered by a package, that can be used to create expressions that resemble abstract syntax trees of density functions for Minecraft: Java Edition.<br>
It allows you to comfortably write density functions while also benefiting from Pythons forgiving syntax.

###### <sub>This project is pretty similar to [misode/gaia-beet](https://github.com/misode/gaia-beet), which you might also find pretty useful, but I started developing Rhombus before knowing of it.<br>The similarities in concept are very frightening though. The biggest difference to Misode's gaia-beet is that I am not so much developing a beet plugin — although integration is given — but rather I view Rhombus as a coherent, albeit simple language, and am trying to further develop and improve it in this sense.</sub>

## Key Advantages
- 📦 **Object Oriented:** All of Pythons features for composing values can be used
- 📝 **Comments:** Since we're writing in Python, you can comment how much you want or need
- 📖 **Documentation:** The docstrings of the functions and classes contain crucial information on the usage
- ⚡ **Performance:** The Code will be transpiled into as few files as possible, so that the chunk generator doesn't waste much ressources on compiling many files every time
- ⚙️ **Compatability:** As long as density function syntax isn't changed completely, compatability is given for all Minecraft versions. Adding support for features from mods also is not too complicated