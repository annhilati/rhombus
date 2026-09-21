__all__ = ["cache", "interpolated", "recurrence_cache", "specified_cache"]

from typing import Callable, Iterable

from rhombus.core import RhombusASTNode, DensityFunction, Reference, uuid_hash
from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro, resolve_ast_versioning

import rhombus.support.vanilla.types as vt

from ._implementations.performance import cache_nodes, df_size_info, DensityFunctionSizeInfo


# NOTE: multiple nested caching functions are no longer auto-inlined. When adding compatability with older versions again, implement it again
@macro
def cache(df: AnyDensity, *, partition: bool = True) -> Density:
    """If this density function is referenced twice, it is only computed once per block position.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#cache)
    """
    if partition:
        return Density.partitioned(vt.cache(df.AST))
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
        target_nodes: Iterable[RhombusASTNode],
    ) -> Callable[[DensityFunction, dict[RhombusASTNode, int]], bool]:
        """Applies if the node is one of the specified target nodes."""
        targets = []
        for n in target_nodes:
            if isinstance(n, Density):
                targets.append(n.AST)
            else:
                targets.append(n)

        def condition(node: DensityFunction, occurrences: dict[RhombusASTNode, int]) -> bool:
            for target in targets:
                if isinstance(target, type) and isinstance(node, target):
                    return True
                if node == target:
                    return True
            return False

        return condition
    
    @staticmethod
    def occurrences_satisfy(validator: Callable[[int], bool]) -> Callable[[DensityFunction, dict[RhombusASTNode, int]], bool]:
        """Applies if the node occurs at least a specified number of times."""
        def condition(node: DensityFunction, occurrences: dict[RhombusASTNode, int]) -> bool:
            return validator(occurrences.get(node, 0))
        return condition
    
    @staticmethod
    def min_size(nodes_count: int) -> Callable[[DensityFunction, dict[RhombusASTNode, int]], bool]:
        """Applies if the node has at least a specified number of toplevel nodes."""
        def condition(node: DensityFunction, occurrences: dict[RhombusASTNode, int]) -> bool:
            return df_size_info(node).toplevel_nodes >= nodes_count
        return condition


@macro
def recurrence_cache(
    df: AnyDensity,
    *,
    caching_function: DensityFunction = vt.cache,
    max_nodes: int = 5,
) -> Density:
    """Applies caching to recurring parts of a density function by partitioning it and wrapping it
    with a caching function.
    
    Parameters:
        caching_function (DensityFunction): The density function type partitioned functions get wrapped in.
        max_nodes (int): Number of nodes a recurring function part must surpass to get partitioned.
    """
    transformer = lambda dfnode: Reference(
        "rhombus:partitioned/" + uuid_hash(dfnode.serialize_toplevel()),
        definition=caching_function(dfnode),
    )
    return Density(
        cache_nodes(
            resolve_ast_versioning(df.AST),
            Conditions.occurrences_satisfy(lambda n: n > 1),
            Conditions.min_size(max_nodes + 1),
            transformer=transformer,
        )[0]
    )


@macro
def specified_cache(
    df: AnyDensity,
    *functions: Density,
    caching_function: type[DensityFunction] = vt.cache,
) -> Density:
    """Applies cahing to specific parts of a density function. All subfunctions
    that are equal to a node specified in `functions` and occur multiple times
    are partitioned and wrapped in a caching function.
    
    Parameters:
        *functions (Density): Subfunctions to cache. (Values not of type `Density` are ignored)
        caching_function (DensityFunction): The density function type partitioned functions get wrapped in.
    """
    transformer = lambda node: Reference(
        "rhombus:partitioned/" + uuid_hash(node.serialize_toplevel()),
        definition=Density(caching_function(node)).AST,
    )
        
    return Density(
        cache_nodes(
            df.AST,
            Conditions.is_one_of([n.AST for n in functions if isinstance(n, Density)]),
            Conditions.occurrences_satisfy(lambda n: n > 1),
            transformer=transformer
        )[0]
    )


def get_size(df: Density) -> DensityFunctionSizeInfo:
    """Returns information about the size of a density function.

    Returns:
        DensityFunctionSizeInfo
            - `~.nodes_uncached`: Number of nodes that are not part of a unique cached subtree
            - `~.nodes_in_unique_cached`: Number of nodes that are part of a unique cached subtree
            - `~.unique_unknown_references`: Number of unique references with unknown definition
            - `~.total_unknown_references`: Total number of references with unknown definition (counting duplicates)
    """
    resolved = resolve_ast_versioning(df.AST)
    return df_size_info(resolved)
