---
title: Datapack Resources
icon: lucide/square-function
---

# Datapack Resources

Datapack Resources are all kind of resources that can be provided by a datapack.

These kind of resources require a separate class, because they cannot be defined inline in a density function definition.

For vanilla, only the `Noise` class, corresponding to the `noise` registry of a datapack is relevant.

## Defining DatapackResource classes

Here is how the standard noise resource is defined:

```py
from Rhombus.core import DatapackResource
from dataclasses import dataclass

@dataclass
class Noise(DatapackResource):

    # The value here has to be a class inheriting from beet.core.file.DataModelBase
    fileclass: ClassVar = WorldgenNoise

    # Declare the fields like for regular dataclasses
    firstOctave: int
    amplitudes:  list[float]
     
    # @classmethod
    # def decode(cls, data: JSONDict) -> Noise: ...
    # def encode(self) -> JSONDict: ...

    # As long as the fields of the DatapackResource correspond one to one to fields in the JSON definition,
    # decode() and encode() methods don't have to be defined, because they're already defined by the base class.
    # However, if a field deviates in its name or several fields deviate in their arrangement,
    # or if types are required that are not trivially supported, these functions must be implemented manually.

    # A sensible __eq__ method is also required
    def __eq__(self, other: Noise):
        if not isinstance(other, Noise):
            return None
        if self.reference is None and other.reference is None:
            return (self.firstOctave == other.firstOctave) and (self.amplitudes == other.amplitudes)
        return self.reference == other.reference

```