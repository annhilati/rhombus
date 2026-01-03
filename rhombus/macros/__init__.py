"""Predefined functions for more complex calculations."""

from rhombus.macros import math, coord

_symbols = [math, coord]
_constants = []

__all__ = [obj.__name__ for obj in _symbols] + _constants