__all__ = ["cache", "interpolated", "new_cache_transformer"]

from typing import Callable, Iterable

from rhombus.core import NewDatapackNode, DensityFunction, Reference, JSON_hash
from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro, implementation

import rhombus.support.vanilla.types as vt

from ._implementations.optimization import node_caching_transformer, df_size_info


# NOTE: multiple nested caching functions are no longer auto-inlined. When adding compatability with older versions again, implement it again
@macro
def cache(df: AnyDensity) -> Density:
    """If this density function is referenced twice, it is only computed once per block position.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#cache)
    """
    @implementation(until=118)
    def cache():
        return Density.partitioned(vt.cache(df.AST))
    @implementation
    def cache():
        return Density(vt.cache(df.AST))


@macro
def interpolated(df: AnyDensity, cell_size_xz: int = 4, cell_size_y: int = 4) -> Density:
    """Interpolates at each block in one cell based on the input density function
    value of some cells around. The size of each cell is 4 by 4.

    **NOTE** `cell_size_xz` and `cell_size_y` only take effect starting with datapack version 118.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#interpolated)
    """
    return Density(vt.interpolated(df.AST, cell_size_xz, cell_size_y))



class Conditions:
    
    @staticmethod
    def is_one_of(
        target_nodes: Iterable[NewDatapackNode],
    ) -> Callable[[DensityFunction, dict[NewDatapackNode, int]], bool]:
        """Applies if the node is one of the specified target nodes."""
        targets = []
        for n in target_nodes:
            if isinstance(n, Density):
                targets.append(n.AST.build())
            elif hasattr(n, "build"):
                targets.append(n.build())
            else:
                targets.append(n)

        def condition(node: DensityFunction, occurrences: dict[NewDatapackNode, int]) -> bool:
            for target in targets:
                if isinstance(target, type) and isinstance(node, target):
                    return True
                if node == target:
                    return True
            return False

        return condition
    
    @staticmethod
    def occurrences_satisfy(validator: Callable[[int], bool]) -> Callable[[DensityFunction, dict[NewDatapackNode, int]], bool]:
        """Applies if the node occurs at least a specified number of times."""
        def condition(node: DensityFunction, occurrences: dict[NewDatapackNode, int]) -> bool:
            return validator(occurrences.get(node, 0))
        return condition
    
    @staticmethod
    def size_satisfies(validator: Callable[[int], bool]) -> Callable[[DensityFunction, dict[NewDatapackNode, int]], bool]:
        """Applies if the node has at least a specified number of toplevel nodes."""
        def condition(node: DensityFunction, occurrences: dict[NewDatapackNode, int]) -> bool:
            return validator(df_size_info(node).toplevel_nodes)
        return condition



@macro
def new_cache_transformer(
    df: AnyDensity,
    *,
    targets: Iterable[AnyDensity] = ...,
    min_size: int = 5,
    min_occurances: int = 2,
    caching_function: DensityFunction | Callable[[DensityFunction], DensityFunction] = vt.cache
) -> Density:
    if targets == ...:
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
        definition=caching_function(node) if not isinstance(caching_function(node), Density) else caching_function(node).AST.build(),
    )
        
    return Density(
        node_caching_transformer(
            df.AST.build(),
            *conditions,
            transformer=transformer
        )[0]
    )