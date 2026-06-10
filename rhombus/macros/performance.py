"""Preliminary functions for evaluating and improving the performance
of density functions.

This is primarily the `autocache` macro, which extracts recurring parts of
the AST of the entered density function and wrapps them in `cache_once`. 
"""

__all__ = ["autocache", "get_size"]


from typing import NamedTuple, Any, Callable
import json

from rhombus.core import DensityFunction, Reference, uuid_hash, RhombusASTNode
from rhombus.std import types, AnyDensity, Density, macro

class DensityFunctionSizeInfo(NamedTuple):
    nodes_uncached: int
    nodes_in_unique_cached: int
    unique_unknown_references: int
    total_unknown_references: int

def _count_node_values(node: RhombusASTNode) -> dict[RhombusASTNode, int]:
    """Recursively count unique nodes.

    Nodes that are equal are grouped.
    """

    if not isinstance(node, RhombusASTNode):
        raise TypeError("Expected RhombusASTNode instance")
    # Use a stable serialized representation as grouping key to avoid
    # relying on object identity or potentially brittle equality semantics.

    counts_by_key: dict[str, int] = {}
    example_node_by_key: dict[str, RhombusASTNode] = {}
    # Use path-local seen set to avoid infinite recursion on cycles while still
    # allowing counting of the same shared node when encountered from multiple
    # parents.

    def canonical_form(value: Any):
        """Create a deterministic, fully expanded representation for grouping."""
        # Primitive JSON values
        if isinstance(value, (str, int, float, bool)) or value is None:
            return ("lit", value)

        # Nodes: represent by class name and ordered fields
        if isinstance(value, RhombusASTNode):
            return (
                type(value).__name__,
                tuple((fname, canonical_form(fval)) for fname, fval in value.fields.items())
            )

        # Collections
        if isinstance(value, dict):
            return ("dict", tuple(sorted((canonical_form(k), canonical_form(v)) for k, v in value.items())))

        if isinstance(value, (list, tuple, set)):
            return ("seq", tuple(canonical_form(v) for v in value))

        # Fallback to string representation
        return ("other", repr(value))

    def key_for(value: RhombusASTNode) -> str:
        return json.dumps(canonical_form(value), sort_keys=True, ensure_ascii=True, separators=(",",":"))

    def visit(value: Any, path_seen: set[int]) -> None:
        if isinstance(value, RhombusASTNode):
            # prevent cycles within the current traversal path
            if id(value) in path_seen:
                return
            new_path = set(path_seen)
            new_path.add(id(value))

            k = key_for(value)
            counts_by_key[k] = counts_by_key.get(k, 0) + 1
            example_node_by_key.setdefault(k, value)

            for child in value.fields.values():
                visit(child, new_path)

        elif isinstance(value, dict):
            for item in value.keys():
                visit(item, path_seen)
            for item in value.values():
                visit(item, path_seen)

        elif isinstance(value, (list, tuple, set)):
            for item in value:
                visit(item, path_seen)

    visit(node, set())

    # convert back to mapping node -> count using one representative node per key
    result: dict[RhombusASTNode, int] = {}
    for k, cnt in counts_by_key.items():
        result[example_node_by_key[k]] = cnt

    return result


def _size(node: DensityFunction) -> DensityFunctionSizeInfo:
    """Gathers information about the size of a density function in terms of number of nodes.

    Returns:
        DensityFunctionSizeInfo
            - `nodes_uncached`: Number of nodes that are not part of a unique cached subtree
            - `nodes_in_unique_cached`: Number of nodes that are part of a unique cached subtree
            - `unique_unknown_references`: Number of unique references with unknown definition
            - `total_unknown_references`: Total number of references with unknown definition (counting duplicates)

    """
    if not isinstance(node, DensityFunction):
        raise TypeError("Expected DensityFunction instance")

    nodes_uncached: int = 0
    nodes_in_unique_cached: int = 0
    unique_unknown_references: set[str] = set()
    total_unknown_references: int = 0

    seen_cachable_references: set[str] = set()

    def visit(value: Any, we_are_in_cached: bool = False) -> None:
        nonlocal nodes_uncached, nodes_in_unique_cached, unique_unknown_references, total_unknown_references

        if isinstance(value, DensityFunction):

            # Case: This is a regular DensityFunction node
            if not we_are_in_cached:
                nodes_uncached += 1
            # Case: This is a DensityFunction node that is part of a unique cached subtree
            else:
                nodes_in_unique_cached += 1

            if isinstance(value, Reference):

                # Case: Reference with unknown definition
                if value.definition is None:
                    unique_unknown_references.add(value.reference)
                    total_unknown_references += 1

                # Case: Reference with known definition
                else:
                    # Case: Reference definition is cachable
                    if isinstance(value.definition, (types.cache_2d, types.cache_all_in_cell, types.cache_once, types.flat_cache)): # TODO: this shouldn't be hardcoded
                        # Case: We have not seen this cachable reference before
                        if value.reference not in seen_cachable_references:
                            seen_cachable_references.add(value.reference)
                            visit(value.definition, we_are_in_cached=True)

                return # We do not want to count the references' fields twice

            for child in value.fields.values():
                visit(child, we_are_in_cached)

        elif isinstance(value, dict):
            for item in value.keys():
                visit(item, we_are_in_cached)
            for item in value.values():
                visit(item, we_are_in_cached)

        elif isinstance(value, (list, tuple, set)):
            for item in value:
                visit(item, we_are_in_cached)

    visit(node)

    return DensityFunctionSizeInfo(
        nodes_uncached=nodes_uncached,
        nodes_in_unique_cached=nodes_in_unique_cached,
        unique_unknown_references=len(unique_unknown_references),
        total_unknown_references=total_unknown_references
    )

def _wrap_redundances(
        root: DensityFunction,
        max_nodes: int = 6,
        wrapper: Callable[[DensityFunction], DensityFunction] = lambda value: Reference("rhombus:generated/" + uuid_hash(value.serialize_toplevel()), definition=types.cache_once(value))
    ) -> tuple[DensityFunction, dict[DensityFunction, int]]:
    """Returns `root` but replaces all recurring sub trees that have a size
    of more than `max_nodes` uncached nodes with partitioned and cached versions.
    """

    occurances = _count_node_values(root)
    replacement_info: dict[DensityFunction, int] = {}

    def clone_node(node: DensityFunction) -> DensityFunction:
        return node.__class__(**{
            field_name: field_value
            for field_name, field_value in node.fields.items()
        })

    def visit_and_replace_if_needed(value: DensityFunction | Any) -> DensityFunction | Any:
        if isinstance(value, DensityFunction):

            # Skip further caching if this is already a reference with cache_once
            if isinstance(value, Reference) and isinstance(value.definition, (types.cache_2d, types.cache_all_in_cell, types.cache_once, types.flat_cache)): # TODO: this shouldn't be hardcoded
                return value

            if occurances[value] > 1 and _size(value).nodes_uncached > max_nodes:
                # Cache this recurring node WITHOUT optimizing its children first
                # This prevents nested cache_once wrappers on child nodes
                reference = wrapper(value)
                replacement_info[value] = 1 if value not in replacement_info else replacement_info[value] + 1
                return reference

            # Not a candidate for caching, so just optimize children
            new = clone_node(value)

            for field_name, field_value in value.fields.items():
                new_value = visit_and_replace_if_needed(field_value)
                setattr(new, field_name, new_value)

            return new

        elif isinstance(value, dict):
            for item in value.keys():
                return visit_and_replace_if_needed(item)
            for item in value.values():
                return visit_and_replace_if_needed(item)

        elif isinstance(value, (list, tuple, set)):
            for item in value:
                return visit_and_replace_if_needed(item)

        return value

    return visit_and_replace_if_needed(root), replacement_info


@macro
def autocache(argument: AnyDensity, *, caching_function: DensityFunction = types.flat_cache) -> Density:
    wrapper = lambda value: Reference("rhombus:generated/" + uuid_hash(value.serialize_toplevel()), definition=caching_function(value))
    return Density(_wrap_redundances(argument.AST, max_nodes=6, wrapper=wrapper)[0])
    # TODO check whether to autocache inside of reference definitions

def get_size(df: Density) -> DensityFunctionSizeInfo:
    return _size(df.AST)