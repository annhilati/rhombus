"""Predefined functions for more complex calculations."""

from rhombus.macros import math 

_symbols = [math]
_constants = []

__all__ = [obj.__name__ for obj in _symbols] + _constants