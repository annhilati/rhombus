---
title: Density Function Types
icon: lucide/square-function
---

# Density Function Types

A density function type represents a kind of operation, which to apply on its arguments. In Rhombus, the subclasses of `DensityFunction` are the nodes of the abstract syntax tree that represents a density function.

## Defining DensityFunction classes

In order for the data for new density function to be stored, a `dataclass` inheriting from `DensityFunction` is needed.
The new class requires the following attributes:

```py
id: ClassVar[str]
    # The identifier of the density function type including its namespace, 
    # like it is used in the `type` field of a density function definition in a datapack. 

decode: ClassVar[Callable[[type[Self], JSONDict], Self]]
    # A `classmethod` that can create an instance of the class
    # from a dictionary(JSON density function definition)

encode: ClassVar[Callable[[Self], JSONDict | float | str]]
    # A method that can create a dictionary (JSON density function definition)
    # from an instance of the class
```

### Base classes

There are some base classes that already implement the `decode` and `encode` methods for common fields like shown as follows.

#### Types with no arguments or one or two density function arguments

There are base classes for density function types that take no arguments or one or two arguments that are density functions.
When inheriting from these, besides stating the function type id, no additional declarations have to be made. The classes are:

- `SimpleFunctionBase` for function types that don't take any arguments
- `MappedFunctionBase` for function types that take an argument `argument` of type `DensityFunction`
- `DoubleArgumentFunctionBase` for function types that take two arguments `argument1` and `argument2` of type `DensityFunction`

=== "No arguments"

    ```py
    class end_islands(SimpleFunctionBase):
        id: ClassVar[str] = "minecraft:end_islands"
    ```
=== "One argument"

    ```py
    class abs(MappedFunctionBase):
        id: ClassVar[str] = "minecraft:abs" 
    ```
=== "Two arguments"

    ```py
    class add(DoubleArgumentFunctionBase): 
        id: ClassVar[str] = "minecraft:add"
    ```

#### Types with any fields of trivial types

For density function types with fields that aren't covered by the base classes above, a `dataclass` declaration inheriting from `MultiArgumentsFunctionBase` has to be made.

The following types are supported in the fields:

- JSON-compatible value types (`str`, `dict`, `list`, `tuple`, `str`, `int`, `float`, `bool`, `None`)
- `DensityFunction`
- `list[DensityFunction]`
- Classes inheriting from `DatapackResource` (like `Noise`)

Fields of `DensityFunction` subclasses must be called exactly like their counterparts in the JSON definition, unless a separate encoding and decoding logic is implemented.

```py
@dataclass # See how the dataclass decorator is required here,
           # because we declare only here what fields the function type has
class shifted_noise(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:shifted_noise"
    noise: Noise
    xz_scale: float
    y_scale: float
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction
```

When a new class inheriting `DensityFunction` is defined, it will automatically be registered in the decoding context.

#### Types with more complex fields

Density function types that require fields of non-trivial types or whose fields should have a different composition than the JSON definition, the required methods have to be implemented manually.

```py
@dataclass
class spline(DensityFunction):
    id: ClassVar[str] = "minecraft:spline"
    coordinate: DensityFunction
    points: list[tuple[float, DensityFunction, float]]

    @classmethod
    def decode(cls, data: JSONDict) -> spline:
        return cls(
            decode_HOLDER_HELPER_CODEC(data["spline"]["coordinate"]),
            [
                (point["location"], decode_HOLDER_HELPER_CODEC(point["value"]), point["derivative"])
                for point in data["spline"]["points"]
            ]
        )
    
    def encode(self) -> JSONDict:
        return {
            "type": self.id,
            "spline": {
                "coordinate": self.coordinate.encode(),
                "points": [
                    {
                        "location": point[0],
                        "value": point[1].encode() if isinstance(point[1], DensityFunction) else point[1],
                        "derivative": point[2], 
                    }
                    for point in self.points
                ]
            }
        }
```