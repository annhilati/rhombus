from typing import overload, Callable, Iterable

from rhombus.core import DensityFunction, Reference, uuid_hash, RhombusASTNode
from rhombus.std.density import Density, AnyDensity, _unify
from rhombus.std.macros import macro
from rhombus.std import coords
from rhombus.support import vanilla as vt, vanilla_legacy as lt

from rhombus.core.environment import env

from ._implementations.performance import count_node_values, cache_nodes, df_size_info, DensityFunctionSizeInfo


# @overload
# def cache_2d(
#     df: AnyDensity, *, partition: bool = True
# ) -> Density[vt.Reference]: ...
# @overload
# def cache_2d(
#     df: AnyDensity, *, partition: bool = False
# ) -> Density[lt.cache_2d]: ...
# @macro
# def cache_2d(df: AnyDensity, *, partition: bool = True):
#     """Only computes the input density once per horizontal position.

#     ---
#     [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#cache_2d)
#     """
#     if partition:
#         if isinstance(df.AST, vt.Reference) and isinstance(
#             df.AST.definition, tuple(env.caching_function_types)
#         ):
#             df = Density(df.AST.definition)
#         return Density.partitioned(lt.cache_2d(df.AST))
#     return Density(lt.cache_2d(df.AST))


# @overload
# def cache_all_in_cell(
#     df: AnyDensity, *, partition: bool = True
# ) -> Density[vt.Reference]: ...
# @overload
# def cache_all_in_cell(
#     df: AnyDensity, *, partition: bool = False
# ) -> Density[lt.cache_all_in_cell]: ...
# @macro
# def cache_all_in_cell(df: AnyDensity, partition: bool = True):
#     """🚨 Should not be used in datapacks.

#     ---

#     Used by the game onto `final_density`.

#     ---
#     [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#cache_all_in_cell)
#     """
#     if partition:
#         if isinstance(df.AST, vt.Reference) and isinstance(
#             df.AST.definition, tuple(env.caching_function_types)
#         ):
#             df = Density(df.AST.definition)
#         return Density.partitioned(lt.cache_all_in_cell(df.AST))
#     return Density(lt.cache_all_in_cell(df.AST))


@overload
def cache(
    df: AnyDensity, *, partition: bool = True
) -> Density[vt.Reference]: ...
@overload
def cache(
    df: AnyDensity, *, partition: bool = False
) -> Density[vt.cache]: ...
@macro
def cache(df: AnyDensity, *, partition: bool = True):
    """If this density function is referenced twice, it is only computed once per block position.

    Does not affect the density value.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#cache)
    """
    if partition:
        if isinstance(df.AST, vt.Reference) and isinstance(
            df.AST.definition, tuple(env.caching_function_types)
        ):
            df = Density(df.AST.definition)
        return Density.partitioned(vt.cache(df.AST))
    return Density(vt.cache(df.AST))


@overload
def flat_cache(
    df: AnyDensity, *, partition: bool = True
) -> Density[vt.Reference]: ...
@overload
def flat_cache(
    df: AnyDensity, *, partition: bool = False
) -> Density[lt.flat_cache]: ...
@macro
def flat_cache(df: AnyDensity, *, partition: bool = True):
    """Calculate the value per 4x4 column (Value at each block in one column is the same). And it is calculated only once per column, at Y=0. Used often in combination with `interpolated`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#flat_cache)
    """
    if env.datapack_version < 118:
        if partition:
            if isinstance(df.AST, vt.Reference) and isinstance(
                df.AST.definition, tuple(env.caching_function_types)
            ):
                df = Density(df.AST.definition)
            return Density.partitioned(lt.flat_cache(df.AST))
        return Density(lt.flat_cache(df.AST))
    return cache(coords.slice(df, y=0))


@macro
def interpolated(df: AnyDensity) -> Density[vt.interpolated]:
    """Interpolates at each block in one cell based on the input density function
    value of some cells around. The size of each cell is 4 by 4.

    It is used in combination with `flat_cache` to compensate for its 4x4 averaging.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#interpolated)
    """
    return Density(vt.interpolated(df.AST))


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
    argument: AnyDensity,
    *,
    caching_function: DensityFunction = cache,
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
    occurances = count_node_values(argument.AST)
    return Density(
        cache_nodes(
            argument.AST,
            condition=_get_occurance_and_size_condition(max_nodes, occurances),
            wrapper=wrapper,
        )[0]
    )


@macro
def specified_cache(
    argument: AnyDensity,
    *functions: Density,
    caching_function: DensityFunction = vt.cache,
) -> Density:
    """Applies cahing to specific parts of a density function. All subfunctions
    that are equal to a node specified in `nodes` and occur multiple times
    are partitioned and wrapped in a caching function.
    
    Parameters:
        *functions (Density): Subfunctions to cache. (Values not of type `Density` are ignored)
        caching_function (DensityFunction): The density function type partitioned functions get wrapped in.
    """
    wrapper = lambda node: Reference(
        "rhombus:partitioned/" + uuid_hash(node.serialize_toplevel()),
        definition=_unify(caching_function(node)),
    )
    occurances = count_node_values(argument.AST)
    identity_cond = _get_identity_condition([n.AST for n in functions if isinstance(n, Density)])
    condition = lambda node: (
        identity_cond(node) and occurances.get(node, 0) > 1
    )
    # Cache if node is one of specified and it occurs multiple times
    return Density(cache_nodes(argument.AST, condition=condition, wrapper=wrapper)[0])


def get_size(df: Density) -> DensityFunctionSizeInfo:
    """Returns information about the size of a density function.

    Returns:
        DensityFunctionSizeInfo
            - `~.nodes_uncached`: Number of nodes that are not part of a unique cached subtree
            - `~.nodes_in_unique_cached`: Number of nodes that are part of a unique cached subtree
            - `~.unique_unknown_references`: Number of unique references with unknown definition
            - `~.total_unknown_references`: Total number of references with unknown definition (counting duplicates)
    """
    return df_size_info(df.AST)
