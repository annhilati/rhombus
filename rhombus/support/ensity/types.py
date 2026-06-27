from typing import ClassVar

from rhombus.core.density_function import SimpleDensityFunction

class floating_islands(SimpleDensityFunction):
    id: ClassVar = "msg:floating_islands"

class lonely_island(SimpleDensityFunction):
    id: ClassVar = "msg:lonely_island"