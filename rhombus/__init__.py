"""A Python embedded DSL for writing Density Functions for Minecraft Datapacks
"""

from rhombus.language import *
from rhombus.toolchain.beet import compile, inject, summon
from rhombus.macros import *
from rhombus.core import config