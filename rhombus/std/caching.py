__all__ = ["cache", "upscale", "optimize"]

from typing import Literal, Callable, Iterable, Any
import warnings

from rhombus.core import DatapackNode, DensityFunction, Reference, RhombusASTNode, JSON_hash
from rhombus.std.builtin.density import Density, AnyDensity
from rhombus.std.builtin.macros import macro, implementation

import rhombus.support.vanilla.types as vt
import rhombus.support.vanilla.legacy_types as lt

from ._implementations.optimization import node_caching_transformer, df_size_info


# NOTE: multiple nested caching functions are no longer auto-inlined. When adding compatability with older versions again, implement it again
@macro
def cache(df: AnyDensity) -> Density:
    """If this density function is referenced twice, it is only computed once per block position.

    **NOTE:** Also consider `caching.optimize()` to automatically cache recurring parts in a `Density`.
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#cache)
    """
    @implementation(until=118)
    def cache():
        return Density.partitioned(vt.cache(df.build()))
    @implementation
    def cache():
        return Density(vt.cache(df.build()))


@macro
def upscale(
    df: AnyDensity,
    x_cell_size: int = 4,
    y_cell_size: int = 8,
    z_cell_size: int = 4,
    x_mode: Literal["nearest_neighbor", "interpolate_linear", "interpolate_cosine", "interpolate_cubic", "b_spline_cubic"] = "interpolate_linear",
    y_mode: Literal["nearest_neighbor", "interpolate_linear", "interpolate_cosine", "interpolate_cubic", "b_spline_cubic"] = "interpolate_linear",
    z_mode: Literal["nearest_neighbor", "interpolate_linear", "interpolate_cosine", "interpolate_cubic", "b_spline_cubic"] = "interpolate_linear",
) -> Density:
    # TODO: extend technical explanation
    """Samples the input function at a reduced resolution, and interpolates on each axis with the specified modes.
    
    ### Modes:
    - `nearest_neighbor` (1 sample) 
    - `interpolate_linear` (2 samples) 
    - `interpolate_cosine` (2 samples) 
    - `interpolate_cubic` (4 samples) 
    - `b_spline_cubic` (4 samples) 
    
    **NOTE:** Upscaling is performed by axis in order: Z, X, then Y.

    **NOTE:** Cell size specifications only take effect starting with datapack version 118.
    For versions below, the cell size is derived from the noise settings. The effective cell sizes for the vanilla dimensions are (in X-Y-Z order):
    - Overworld: 4×8×4
    - Nether: 4×8×4
    - The End: 8×4×8
    
    **NOTE:** Mode specifications only take effect starting with datapack version 125.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#interpolated)
    """
    @implementation(until=118)
    def interpolated():
        if any(mode != "interpolate_linear" for mode in (x_mode, y_mode, z_mode)):
            warnings.warn("In datapack versions before 125 the interpolation mode cannot be set. A procedure identical to the 'interpolate_linear' mode will be used instead.")
        warnings.warn("In datapack versions before 118 the interpolation cell size is derived from the noise settings. Passed cell size parameters will not take effect.")
        return Density(lt.interpolated(df.build()))
    @implementation(until=125)
    def interpolated():
        if any(mode != "interpolate_linear" for mode in (x_mode, y_mode, z_mode)):
            warnings.warn("In datapack versions before 125 the interpolation mode cannot be set. A procedure identical to the 'interpolate_linear' mode will be used instead.")
        if x_cell_size != z_cell_size:
            raise ValueError("In datapack versions before 125 the cell sizes for the X and Z axes must be identical.")
        return Density(lt.interpolated(df.build(), cell_size_xz=x_cell_size, cell_size_y=y_cell_size))
    @implementation
    def upscale():
        return Density(vt.upscale(
            df.build(),
            x=vt.AxisScaling(x_mode, x_cell_size),
            y=vt.AxisScaling(y_mode, y_cell_size),
            z=vt.AxisScaling(z_mode, z_cell_size),
        ))



class Conditions:
    
    @staticmethod
    def is_one_of(
        target_nodes: Iterable[Density | DatapackNode | RhombusASTNode[DensityFunction]],
    ) -> Callable[[DensityFunction, dict[DatapackNode, int]], bool]:
        """Applies if the node is one of the specified target nodes."""
        targets = []
        for n in target_nodes:
            if isinstance(n, Density):
                targets.append(n.build())
            elif isinstance(n, RhombusASTNode):
                targets.append(n.build())
            else:
                targets.append(n)

        def condition(node: DensityFunction, occurrences: dict[DatapackNode, int]) -> bool:
            for target in targets:
                if isinstance(target, type) and isinstance(node, target):
                    return True
                if node == target:
                    return True
            return False

        return condition
    
    @staticmethod
    def occurrences_satisfy(validator: Callable[[int], bool]) -> Callable[[DensityFunction, dict[DatapackNode, int]], bool]:
        """Applies if the node occurs at least a specified number of times."""
        def condition(node: DensityFunction, occurrences: dict[DatapackNode, int]) -> bool:
            return validator(occurrences.get(node, 0))
        return condition
    
    @staticmethod
    def size_satisfies(validator: Callable[[int], bool]) -> Callable[[DensityFunction, dict[DatapackNode, int]], bool]:
        """Applies if the node has at least a specified number of toplevel nodes."""
        def condition(node: DensityFunction, occurrences: dict[DatapackNode, int]) -> bool:
            return validator(df_size_info(node).toplevel_nodes)
        return condition



@macro
def optimize(
    df: AnyDensity,
    *,
    targets: Iterable[AnyDensity] = Any,
    min_size: int = 5,
    min_occurances: int = 2,
    caching_function: DensityFunction | Callable[[DensityFunction], DensityFunction | Density] = vt.cache
) -> Density:
    """The caching optimizer transforms a `Density`, such that it performs better by
    wrapping certain parts of the density function's abstract syntax tree in a caching function.
    
    The wrapper `caching_function` is applied to all AST-parts that
    - consist of at least `min_size` nodes,
    - occur at least `min_occurances` times in `df` and
    - are specified in `targets` if it has been set at all.
    """
    if targets is Any:
        targets: Iterable[AnyDensity] = ()
        
    targets_list = [n.AST for n in targets if isinstance(n, Density)]
    
    conditions = [
        Conditions.size_satisfies(lambda n: n >= min_size),
        Conditions.occurrences_satisfy(lambda n: n >= min_occurances)
    ]
    
    if targets_list:
        conditions.append(Conditions.is_one_of(targets_list))
        
    transformer: Callable[[DensityFunction], DensityFunction] = lambda node: Reference(
        "rhombus:generated/" + JSON_hash(node.serialize_toplevel()),
        definition=caching_function(node) if not isinstance(caching_function(node), Density) else caching_function(node).build(),
    )
        
    return Density(
        node_caching_transformer(
            df.build(),
            *conditions,
            transformer=transformer
        )[0]
    )