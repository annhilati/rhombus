"""Provides backward compatibility for Minecraft world generation features that have been altered or removed.

This module restores legacy density functions and noise types to maintain compatibility with older world designs.
When importing from this module, ensure it is done after importing standard symbols to avoid conflicts.
"""

from .functions import *
from . import types