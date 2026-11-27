__all__ = ["node_caching_transformer", "Conditions"]


from typing import Any, Iterable, Callable
import dataclasses
import sys

from rhombus.core import DatapackNode, RhombusASTNode, DensityFunction, Reference, walk
from rhombus.engine.analysis import count_node_values
from rhombus.std.builtin.density import Density
import rhombus.library.vanilla.types as vt


# Datapack density functions can have exceptionally deep ASTs.
# We bump the recursion limit to prevent crashes during tree traversals and recursive hashing.
if sys.getrecursionlimit() < 10000:
    sys.setrecursionlimit(10000)




def node_caching_transformer(
    root: DensityFunction,
    *conditions: Callable[[DensityFunction, dict[DatapackNode, int]], bool],
    transformer: Callable[[DensityFunction], DensityFunction],
) -> tuple[DensityFunction, dict[DensityFunction, int]]:
    occurrences = count_node_values(root)
    replacement_info: dict[DensityFunction, int] = {}
    memo: dict[tuple[int, frozenset], Any] = {}

    def visit_and_replace_if_needed(
        value: DensityFunction | Any,
        nodes_being_cached: frozenset[DensityFunction] = frozenset(),
    ) -> DensityFunction | Any:
        memo_key = (id(value), nodes_being_cached)
        if memo_key in memo:
            return memo[memo_key]

        if isinstance(value, DensityFunction):
            is_already_cached_ref = isinstance(value, Reference) and isinstance(
                value.definition, vt.cache
            )

            new_nodes_being_cached = nodes_being_cached
            should_cache = (
                not is_already_cached_ref
                and value not in nodes_being_cached
                and all(cond(value, occurrences) for cond in conditions)
            )

            if should_cache:
                new_nodes_being_cached = nodes_being_cached | frozenset([value])
            elif is_already_cached_ref and hasattr(value.definition, "input"):
                new_nodes_being_cached = nodes_being_cached | frozenset([value.definition.input])

            # Recursively optimize children
            current_fields = value.fields
            new_fields = {
                field_name: visit_and_replace_if_needed(field_value, new_nodes_being_cached)
                for field_name, field_value in current_fields.items()
            }
            if any(new_fields[fn] is not fv for fn, fv in current_fields.items()):
                optimized_value = dataclasses.replace(value, **new_fields)
            else:
                optimized_value = value

            if should_cache:
                replacement_info[value] = replacement_info.get(value, 0) + 1
                res = transformer(optimized_value)
            else:
                res = optimized_value

            memo[memo_key] = res
            return res

        # If the value is a standard Python collection, we simply traverse the elements recursively.
        elif isinstance(value, dict):
            res = {
                visit_and_replace_if_needed(
                    k, nodes_being_cached
                ): visit_and_replace_if_needed(v, nodes_being_cached)
                for k, v in value.items()
            }
            memo[memo_key] = res
            return res

        elif isinstance(value, (list, tuple, set, frozenset)):
            res = type(value)(
                [
                    visit_and_replace_if_needed(item, nodes_being_cached)
                    for item in value
                ]
            )
            memo[memo_key] = res
            return res

        memo[memo_key] = value
        return value

    return visit_and_replace_if_needed(root), replacement_info


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
            count = sum(1 for sub in walk(node) if isinstance(sub, DensityFunction) and not isinstance(sub, Reference))
            return validator(count)
        return condition
    
    @staticmethod
    def is_of_type(*types: DatapackNode) -> Callable[[DensityFunction, dict[DatapackNode, int]], bool]:
        """Applies if the node is of one of specified types."""
        def condition(node: DensityFunction, occurrences: dict[DatapackNode, int]) -> bool:
            return isinstance(node, types)
        return condition