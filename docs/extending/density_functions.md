---
title: Mod Support
icon: lucide/square-function
---

# Adding Support for Density Function Types from Mods

Support for any density function types from mods can be added without any problems.

## Register a new class

In order for the data for the new density function to be stored, a `dataclass` inheriting from `DensityFunction` is needed.
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

There are some base classes that already implement the `decode` and `encode` methods for common fields:

- `SimpleFunctionBase` for function types that don't take any arguments
- `MappedFunctionBase` for function types that take an argument `argument` (which must not be declared)
- `DoubleArgumentFunctionBase` for function types that take two arguments `argument1` and `argument2` (which must not be declared)
- `MultiArgumentsFunctionBase` for function types that take any argument (which must be declared as `dataclass` fields) of the following types:
    - JSON-compatible value types (`str`, `dict`, `list`, `tuple`, `str`, `int`, `float`, `bool`, `None`)
    - `DensityFunction` or `list[DensityFunction]`
    - Classes inheriting from `RegistryResource` (like `Noise`)

Fields of `DensityFunction` subclasses must be called exactly like their counterparts in the JSON definition, unless a separate encoding and decoding logic is implemented.

!!! example "Examples from the function types available in vanilla"

    === "end_islands"

        ```py
        class end_islands(SimpleFunctionBase):
            id: ClassVar[str] = "minecraft:end_islands"
        ```
    === "abs"

        ```py
        class abs(MappedFunctionBase):
            id: ClassVar[str] = "minecraft:abs" 
        ```
    === "add"

        ```py
        class add(DoubleArgumentFunctionBase): 
            id: ClassVar[str] = "minecraft:add"
        ```
    === "shifted_noise"

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
    === "spline"

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

When a new class inheriting `DensityFunction` is defined, it will automatically be registered in the decoding context.

## Create a macro

`DensityFunction` classes normally should not be accessible to the user.
To let density function developers use the new density function type in Rhombus, a macro is needed that produces a `Density` object with adequate content.

For how to create such a macro, see [Creating Macros](macros.md).