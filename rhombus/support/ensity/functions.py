from rhombus.language.density import Density
from . import dft


def lonely_island() -> Density[dft.lonely_island]:
    return Density(dft.lonely_island())

def floating_islands() -> Density[dft.floating_islands]:
    return Density(dft.floating_islands())