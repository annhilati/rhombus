__all__ = ["cache", "interpolated", "optimize"]

from typing import Callable, Iterable, Any

from rhombus.core import DatapackNode, DensityFunction, Reference, RhombusASTNode, JSON_hash
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
        return Density.partitioned(vt.cache(df.build()))
    @implementation
    def cache():
        return Density(vt.cache(df.build()))


@macro
def interpolated(df: AnyDensity, cell_size_xz: int = 4, cell_size_y: int = 4) -> Density:
    # TODO: Improve technical explanation
    """Interpolates at each block in one cell based on the input density function
    value of some cells around.

    **NOTE:** `cell_size_xz` and `cell_size_y` only take effect starting with datapack version 118.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#interpolated)
    """
    return Density(vt.interpolated(df.build(), cell_size_xz, cell_size_y))



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