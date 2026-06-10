"""# Rhombus macro library
Macros are functions with arbitrary arguments that return a `Density` object. They
are useful for abstracting away common patterns and making code more readable. 
"""

from rhombus.macros import (
    conditional, performance,
    math, smath, emath,
    coords,
)