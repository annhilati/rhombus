from typing import Any, TypeAlias

strDensityFunctionReference: TypeAlias = str

class DensityFunctionTypeBase:
    "Base class for density function types."
    id: str

    @classmethod
    def as_density_function(cls, parameters: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": cls.id,
            **{
                key: value.as_density_function() if getattr(value, "as_density_function", None) else value
                for key, value
                in parameters.items()
            }
        }
    
class Reference(DensityFunctionTypeBase):
    
    @classmethod
    def as_density_function(cls, parameters: dict[str: Any]) -> str:
        return parameters["argument"]

class abs(DensityFunctionTypeBase):
    id = "minecraft:abs" 

class add(DensityFunctionTypeBase): 
    id = "minecraft:add"

class beardifier(DensityFunctionTypeBase):
    id = "minecraft:beardifier"

class blend_alpha(DensityFunctionTypeBase):
    id = "minecraft:blend_alpha"

class blend_density(DensityFunctionTypeBase):
    id = "minecraft:blend_density"

class blend_offset(DensityFunctionTypeBase):
    id = "minecraft:blend_offset"

class cache_2d(DensityFunctionTypeBase):
    id = "minecraft:cache_2d"

class cache_all_in_cell(DensityFunctionTypeBase):
    id = "minecraft:cache_all_in_cell"

class cache_once(DensityFunctionTypeBase):
    id = "minecraft:cache_once"

class clamp(DensityFunctionTypeBase):
    id = "minecraft:clamp"

class constant(DensityFunctionTypeBase):
    id = "minecraft:constant"

    @classmethod
    def as_density_function(cls, parameters: dict[str: Any]):
        return parameters["argument"]

class cube(DensityFunctionTypeBase):
    id = "minecraft:cube"

class end_islands(DensityFunctionTypeBase):
    id = "minecraft:end_islands"

class find_top_surface(DensityFunctionTypeBase):
    id = "minecraft:find_top_surface"

class flat_cache(DensityFunctionTypeBase):
    id = "minecraft:flat_cache"

class half_negative(DensityFunctionTypeBase):
    id = "minecraft:half_negative"

class interpolated(DensityFunctionTypeBase):
    id = "minecraft:interpolated"

class invert(DensityFunctionTypeBase):
    id = "minecraft:invert"

class max(DensityFunctionTypeBase):
    id = "minecraft:max"

class min(DensityFunctionTypeBase):
    id = "minecraft:min"

class mul(DensityFunctionTypeBase):
    id = "minecraft:mul"

class noise(DensityFunctionTypeBase):
    id = "minecraft:noise"

    @classmethod
    def as_density_function(cls, parameters):
        return {
            "type": cls.id,
            "noise": parameters["noise"].name,
            "xz_scale": parameters["xz_scale"],
            "y_scale": parameters["y_scale"],
        }

class old_blended_noise(DensityFunctionTypeBase):
    id = "minecraft:old_blended_noise"

class quarter_negative(DensityFunctionTypeBase):
    id = "minecraft:quarter_negative"

class range_choice(DensityFunctionTypeBase):
    id = "minecraft:range_choice"

class shift(DensityFunctionTypeBase):
    id = "minecraft:shift"

class shift_a(DensityFunctionTypeBase):
    id = "minecraft:shift_a"

class shift_b(DensityFunctionTypeBase):
    id = "minecraft:shift_b"

class shifted_noise(DensityFunctionTypeBase):
    id = "minecraft:shifted_noise"

class spline(DensityFunctionTypeBase):
    id = "minecraft:spline"

    @classmethod
    def as_density_function(cls, parameters: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": cls.id,
            "spline": {
                "coordinate": parameters["spline"]["coordinate"],
                "points": [
                    {
                        "location": point[0],
                        "value": point[1].as_density_function() if getattr(point[1], "as_density_function", None) else point[1],
                        "derivative": point[2], 
                    }
                    for point in parameters["spline"]["points"]
                ]
            }
        }

class square(DensityFunctionTypeBase):
    id = "minecraft:square"

class squeeze(DensityFunctionTypeBase):
    id = "minecraft:squeeze"

class weird_scaled_sampler(DensityFunctionTypeBase):
    id = "minecraft:weird_scaled_sampler"

class y_clamped_gradient(DensityFunctionTypeBase):
    id = "minecraft:y_clamped_gradient"