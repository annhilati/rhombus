__all__ = ["cache", "interpolated", "recurrence_cache", "specified_cache"]

from typing import Callable, Iterable

from rhombus.core import RhombusASTNode, DensityFunction, Reference, uuid_hash
from rhombus.std.density import Density, AnyDensity, _unify
from rhombus.std.macros import macro, resolve_ast_versioning

from rhombus.support import vanilla as vt

from ._implementations.performance import count_node_values, cache_nodes, df_size_info, DensityFunctionSizeInfo


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


def _get_occurance_and_size_condition(
    max_nodes: int,
    occurances: dict[RhombusASTNode, int],
) -> Callable[[DensityFunction], bool]:
    "Applies if the node exceeds a specified size and occurs multiple times."

    def condition(node: DensityFunction) -> bool:
        return (
            occurances.get(node, 0) > 1
            and df_size_info(node).toplevel_nodes > max_nodes
        )

    return condition


def _get_identity_condition(
    target_nodes: Iterable[RhombusASTNode],
) -> Callable[[DensityFunction], bool]:
    "Applies if the node is one of the specified target nodes."
    targets = []
    for n in target_nodes:
        if isinstance(n, Density):
            targets.append(n.AST)
        else:
            targets.append(n)

    def condition(node: DensityFunction) -> bool:
        for target in targets:
            if isinstance(target, type) and isinstance(node, target):
                return True
            if node == target:
                return True
        return False

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
        max_nodes (int): Number of nodes a recurring function part must have to get partitioned.
    """
    wrapper = lambda value: Reference(
        "rhombus:partitioned/" + uuid_hash(value.serialize_toplevel()),
        definition=caching_function(value),
    )
    occurances = count_node_values(df.AST)
    return Density(
        cache_nodes(
            df.AST,
            condition=_get_occurance_and_size_condition(max_nodes, occurances),
            wrapper=wrapper,
        )[0]
    )


@macro
def specified_cache(
    df: AnyDensity,
    *functions: Density,
    caching_function: DensityFunction = vt.cache,
) -> Density:
    """Applies cahing to specific parts of a density function. All subfunctions
    that are equal to a node specified in `functions` and occur multiple times
    are partitioned and wrapped in a caching function.
    
    Parameters:
        *functions (Density): Subfunctions to cache. (Values not of type `Density` are ignored)
        caching_function (DensityFunction): The density function type partitioned functions get wrapped in.
    """
    wrapper = lambda node: Reference(
        "rhombus:partitioned/" + uuid_hash(node.serialize_toplevel()),
        definition=_unify(caching_function(node)),
    )
    from rhombus.std.macros import resolve_ast_versioning
    resolved_ast = resolve_ast_versioning(df.AST)
    occurances = count_node_values(resolved_ast)
    identity_cond = _get_identity_condition([resolve_ast_versioning(n.AST) for n in functions if isinstance(n, Density)])
    condition = lambda node: (
        identity_cond(node) and occurances.get(node, 0) > 1
    )
    # Cache if node is one of specified and it occurs multiple times
    return Density(cache_nodes(resolved_ast, condition=condition, wrapper=wrapper)[0])


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
