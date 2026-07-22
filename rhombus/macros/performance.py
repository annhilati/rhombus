"""Macros for evaluating and improving the performance of density functions."""

__all__ = ["recurrence_cache", "specified_cache", "get_size"]


from typing import NamedTuple, Any, Callable, Iterable
import dataclasses
import json
import sys

# Datapack density functions can have exceptionally deep ASTs (400+ nodes deep).
# We bump the recursion limit to prevent crashes during tree traversals and recursive hashing.
if sys.getrecursionlimit() < 10000:
    sys.setrecursionlimit(10000)

from beet.contrib import worldgen as beet_worldgen

from rhombus.core import DensityFunction, Reference, uuid_hash, RhombusASTNode
from rhombus.std import AnyDensity, Density, macro
from rhombus.std.types import cache_once
from rhombus.core.environment import env


class DensityFunctionSizeInfo(NamedTuple):
    toplevel_nodes: int
    unique_cached_nodes: int
    unique_unknown_references: int
    total_unknown_references: int


def _count_node_values(node: RhombusASTNode) -> dict[RhombusASTNode, int]:
    """Recursively count unique nodes.

    Nodes that are equal are grouped.
    """

    if not isinstance(node, RhombusASTNode):
        raise TypeError("Expected RhombusASTNode instance")

    counts_by_key: dict[str, int] = {}
    example_node_by_key: dict[str, RhombusASTNode] = {}

    node_keys: dict[int, Any] = {}  # id -> canonical form

    def get_canonical(value: Any, seen: set[int] | None = None):
        """Create a deterministic, fully expanded representation for grouping."""
        if isinstance(value, (str, int, float, bool)) or value is None:
            return ("lit", value)

        val_id = id(value)
        if val_id in node_keys:
            return node_keys[val_id]

        if seen is None:
            seen = set()

        if val_id in seen:
            return ("cycle", val_id)

        new_seen = seen | {val_id}

        if isinstance(value, RhombusASTNode):
            res = (
                type(value).__name__,
                tuple(
                    (fname, get_canonical(fval, new_seen))
                    for fname, fval in value.fields.items()
                ),
            )
        elif isinstance(value, dict):
            res = (
                "dict",
                tuple(
                    sorted(
                        (get_canonical(k, new_seen), get_canonical(v, new_seen))
                        for k, v in value.items()
                    )
                ),
            )
        elif isinstance(value, (list, tuple, set)):
            res = ("seq", tuple(get_canonical(v, new_seen) for v in value))
        else:
            res = ("other", repr(value))

        node_keys[val_id] = res
        return res

    def visit(value: Any, path_seen: set[int]) -> None:
        val_id = id(value)
        if val_id in path_seen:
            return

        new_path = path_seen | {val_id}

        # Visit children first (post-order traversal).
        # This ensures get_canonical only needs 1 level of recursion for already visited children!
        if isinstance(value, RhombusASTNode):
            for child in value.fields.values():
                visit(child, new_path)

            form = get_canonical(value)
            k = json.dumps(
                form, sort_keys=True, ensure_ascii=True, separators=(",", ":")
            )
            counts_by_key[k] = counts_by_key.get(k, 0) + 1
            example_node_by_key.setdefault(k, value)

        elif isinstance(value, dict):
            for k, v in value.items():
                visit(k, new_path)
                visit(v, new_path)

        elif isinstance(value, (list, tuple, set)):
            for item in value:
                visit(item, new_path)

    visit(node, set())

    # convert back to mapping node -> count using one representative node per key
    result: dict[RhombusASTNode, int] = {}
    for k, cnt in counts_by_key.items():
        result[example_node_by_key[k]] = cnt

    return result


def _df_size_info(node: DensityFunction) -> DensityFunctionSizeInfo:

    if not isinstance(node, DensityFunction):
        raise TypeError("Expected DensityFunction instance")

    count_toplevel_nodes: int = 0
    count_unique_cached_nodes: int = 0
    count_total_unknown_references: int = 0
    collect_unique_unknown_references: set[str] = set()

    files = {
        f[0]: f[1]
        for f in Density(node).compile("rhombus:main")
        if isinstance(f[1], beet_worldgen.WorldgenDensityFunction)
    }
    reference_definitions: dict[str, DensityFunction] = {
        ref.identifier: ref.definition
        for ref in node.inscribed_toplevel_nodes
        if isinstance(ref, Reference) and ref.definition is not None
    }
    visited_references: set[str] = set()

    def visit(value: Any, we_are_in_cached: bool = False) -> None:
        nonlocal \
            count_toplevel_nodes, \
            count_unique_cached_nodes, \
            collect_unique_unknown_references, \
            count_total_unknown_references

        if isinstance(value, DensityFunction):
            if not isinstance(value, Reference):
                if not we_are_in_cached:
                    count_toplevel_nodes += 1
                else:
                    count_unique_cached_nodes += 1

            if isinstance(value, Reference):
                if value.definition is not None:
                    if value.identifier not in visited_references:
                        visited_references.add(value.identifier)
                        visit(value.definition, we_are_in_cached=we_are_in_cached)
                    return

                if value.identifier in reference_definitions:
                    if value.identifier not in visited_references:
                        visited_references.add(value.identifier)
                        visit(
                            reference_definitions[value.identifier],
                            we_are_in_cached=we_are_in_cached,
                        )
                    return

                if value.identifier in visited_references:
                    return

                if files.get(value.identifier):
                    visited_references.add(value.identifier)
                    visit(
                        Density.from_dict(files[value.identifier].data).AST,
                        we_are_in_cached=we_are_in_cached,
                    )
                else:
                    collect_unique_unknown_references.add(value.identifier)
                    count_total_unknown_references += 1
                return

            if isinstance(value, tuple(env.caching_function_types)):
                we_are_in_cached = True
            for node in value.fields.values():
                visit(node, we_are_in_cached=we_are_in_cached)

        elif isinstance(value, dict):
            for item in value.keys():
                visit(item, we_are_in_cached)
            for item in value.values():
                visit(item, we_are_in_cached)

        elif isinstance(value, (list, tuple, set)):
            for item in value:
                visit(item, we_are_in_cached)

    visit(Density.from_dict(files["rhombus:main"].data).AST)

    return DensityFunctionSizeInfo(
        toplevel_nodes=count_toplevel_nodes,
        unique_cached_nodes=count_unique_cached_nodes,
        unique_unknown_references=len(collect_unique_unknown_references),
        total_unknown_references=count_total_unknown_references,
    )


def _cache_nodes(
    root: DensityFunction,
    condition: Callable[[DensityFunction], bool],
    wrapper: Callable[[DensityFunction], DensityFunction] = lambda df: Reference(
        "rhombus:partitioned/" + uuid_hash(df.serialize_toplevel()),
        definition=cache_once(df),
    ),
) -> tuple[DensityFunction, dict[DensityFunction, int]]:
    replacement_info: dict[DensityFunction, int] = {}

    def visit_and_replace_if_needed(
        value: DensityFunction | Any,
        nodes_being_cached: frozenset[DensityFunction] = frozenset(),
    ) -> DensityFunction | Any:
        # Check if the current value is a DensityFunction node.
        if isinstance(value, DensityFunction):
            is_already_cached_ref = isinstance(value, Reference) and isinstance(
                value.definition, tuple(env.caching_function_types)
            )

            # If the node has NOT already been manually wrapped in a cache wrapper,
            # AND the specified condition is met (e.g., because it occurs frequently or is the target of `cacheall`),
            # AND it is not already cached by a wrapper higher up in the tree (to prevent double caching):
            if (
                not is_already_cached_ref
                and condition(value)
                and value not in nodes_being_cached
            ):
                # First, recursively optimize the node's inner children
                # before caching the entire node.
                optimized_value, inner_replacements = _cache_nodes(
                    value, condition, wrapper
                )

                for k, v in inner_replacements.items():
                    replacement_info[k] = replacement_info.get(k, 0) + v

                replacement_info[value] = replacement_info.get(value, 0) + 1

                # Place the optimized node in the caching wrapper and return it.
                return wrapper(optimized_value)

            new_nodes_being_cached = nodes_being_cached

            # If the current node is already a caching reference (e.g., set by the user or in a previous step),
            # then we add the inner argument to the “blacklist” (nodes_being_cached).
            # This prevents us from accidentally caching this argument again when traversing down into the children.
            if is_already_cached_ref and hasattr(value.definition, "argument"):
                new_nodes_being_cached = nodes_being_cached | frozenset(
                    [value.definition.argument]
                )

            # The current node is not cached (here). Either the condition did not match,
            # or it was already cached. Build a new node with recursively optimized fields.
            return dataclasses.replace(
                value,
                **{
                    field_name: visit_and_replace_if_needed(
                        field_value, new_nodes_being_cached
                    )
                    for field_name, field_value in value.fields.items()
                },
            )

        # If the value is a standard Python collection, we simply traverse the elements recursively.
        elif isinstance(value, dict):
            return {
                visit_and_replace_if_needed(
                    k, nodes_being_cached
                ): visit_and_replace_if_needed(v, nodes_being_cached)
                for k, v in value.items()
            }

        elif isinstance(value, (list, tuple, set, frozenset)):
            return type(value)(
                [
                    visit_and_replace_if_needed(item, nodes_being_cached)
                    for item in value
                ]
            )

        return value

    return visit_and_replace_if_needed(root), replacement_info


def _get_occurance_and_size_condition(
    max_nodes: int,
    occurances: dict[RhombusASTNode, int],
) -> Callable[[DensityFunction], bool]:
    "Applies if the node exceeds a specified size and occurs multiple times."

    def condition(node: DensityFunction) -> bool:
        return (
            occurances.get(node, 0) > 1
            and _df_size_info(node).toplevel_nodes > max_nodes
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
    caching_function: DensityFunction = cache_once,
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
    occurances = _count_node_values(argument.AST)
    return Density(
        _cache_nodes(
            argument.AST,
            condition=_get_occurance_and_size_condition(max_nodes, occurances),
            wrapper=wrapper,
        )[0]
    )


@macro
def specified_cache(
    argument: AnyDensity,
    *functions: Density,
    caching_function: DensityFunction = cache_once,
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
        definition=caching_function(node),
    )
    occurances = _count_node_values(argument.AST)
    identity_cond = _get_identity_condition([n.AST for n in functions if isinstance(n, Density)])
    condition = lambda node: (
        identity_cond(node) and occurances.get(node, 0) > 1
    )
    # Cache if node is one of specified and it occurs multiple times
    return Density(_cache_nodes(argument.AST, condition=condition, wrapper=wrapper)[0])


def get_size(df: Density) -> DensityFunctionSizeInfo:
    """Returns information about the size of a density function.

    Returns:
        DensityFunctionSizeInfo
            - `~.nodes_uncached`: Number of nodes that are not part of a unique cached subtree
            - `~.nodes_in_unique_cached`: Number of nodes that are part of a unique cached subtree
            - `~.unique_unknown_references`: Number of unique references with unknown definition
            - `~.total_unknown_references`: Total number of references with unknown definition (counting duplicates)
    """
    return _df_size_info(df.AST)
