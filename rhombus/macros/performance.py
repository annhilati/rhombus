"""Preliminary functions for evaluating and improving the performance
of density functions.

This is primarily the `autocache` macro, which extracts recurring parts of
the AST of the entered density function and wrapps them in `cache_once`. 
"""

__all__ = ["autocache", "get_size"]


from typing import NamedTuple, Any, Callable
import json
import sys

# Datapack density functions can have exceptionally deep ASTs (400+ nodes deep).
# We bump the recursion limit to prevent crashes during tree traversals and recursive hashing.
if sys.getrecursionlimit() < 10000:
    sys.setrecursionlimit(10000)

from rhombus.core import DensityFunction, Reference, uuid_hash, RhombusASTNode
from rhombus.std import types, AnyDensity, Density, macro

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
    
    node_keys: dict[int, Any] = {} # id -> canonical form

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
                tuple((fname, get_canonical(fval, new_seen)) for fname, fval in value.fields.items())
            )
        elif isinstance(value, dict):
            res = ("dict", tuple(sorted((get_canonical(k, new_seen), get_canonical(v, new_seen)) for k, v in value.items())))
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
            k = json.dumps(form, sort_keys=True, ensure_ascii=True, separators=(",",":"))
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

    files = Density(node).compile("rhombus:main")
    reference_definitions: dict[str, DensityFunction] = {
        ref.reference: ref.definition
        for ref in node.inscribed_toplevel_nodes
        if isinstance(ref, Reference) and ref.definition is not None
    }
    visited_references: set[str] = set()

    def visit(value: Any, we_are_in_cached: bool = False) -> None:
        nonlocal count_toplevel_nodes, count_unique_cached_nodes, collect_unique_unknown_references, count_total_unknown_references

        if isinstance(value, DensityFunction):

            if not isinstance(value, Reference):
                if not we_are_in_cached:
                    count_toplevel_nodes += 1
                else:
                    count_unique_cached_nodes += 1

            if isinstance(value, Reference):
                if value.definition is not None:
                    if value.reference not in visited_references:
                        visited_references.add(value.reference)
                        visit(value.definition, we_are_in_cached=we_are_in_cached)
                    return

                if value.reference in reference_definitions:
                    if value.reference not in visited_references:
                        visited_references.add(value.reference)
                        visit(reference_definitions[value.reference], we_are_in_cached=we_are_in_cached)
                    return

                if value.reference in visited_references:
                    return

                if files.get(value.reference):
                    visited_references.add(value.reference)
                    visit(Density.from_dict(files[value.reference].data).AST, we_are_in_cached=we_are_in_cached)
                else:
                    collect_unique_unknown_references.add(value.reference)
                    count_total_unknown_references += 1
                return

            if isinstance(value, (types.cache_2d, types.cache_all_in_cell, types.cache_once, types.flat_cache)): # TODO This should not be hardcoded
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
        total_unknown_references=count_total_unknown_references
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

    def visit_and_replace_if_needed(value: DensityFunction | Any, nodes_being_cached: frozenset[DensityFunction] = frozenset()) -> DensityFunction | Any:
        if isinstance(value, DensityFunction):

            is_already_cached_ref = isinstance(value, Reference) and isinstance(value.definition, (types.cache_2d, types.cache_all_in_cell, types.cache_once, types.flat_cache)) # TODO: this shouldn't be hardcoded

            if not is_already_cached_ref and occurances.get(value, 0) > 1 and _df_size_info(value).toplevel_nodes > max_nodes and value not in nodes_being_cached:
                # Cache this recurring node, but first optimize its internal redundancies!
                # By running _wrap_redundances on it as a new root, we find subtrees
                # that recur *within* this node, without redundantly caching nodes that 
                # only recur globally.
                optimized_value, inner_replacements = _wrap_redundances(value, max_nodes=max_nodes, wrapper=wrapper)
                
                for k, v in inner_replacements.items():
                    replacement_info[k] = replacement_info.get(k, 0) + v
                    
                replacement_info[value] = replacement_info.get(value, 0) + 1
                return wrapper(optimized_value)

            new_nodes_being_cached = nodes_being_cached
            if is_already_cached_ref and hasattr(value.definition, "argument"):
                new_nodes_being_cached = nodes_being_cached | frozenset([value.definition.argument])

            # Not a candidate for caching, so just optimize children
            new = clone_node(value)

            for field_name, field_value in value.fields.items():
                new_value = visit_and_replace_if_needed(field_value, new_nodes_being_cached)
                setattr(new, field_name, new_value)

            return new

        elif isinstance(value, dict):
            return {
                visit_and_replace_if_needed(k, nodes_being_cached): visit_and_replace_if_needed(v, nodes_being_cached)
                for k, v in value.items()
            }

        elif isinstance(value, list):
            return [visit_and_replace_if_needed(item, nodes_being_cached) for item in value]
        elif isinstance(value, tuple):
            return tuple(visit_and_replace_if_needed(item, nodes_being_cached) for item in value)
        elif isinstance(value, set):
            return {visit_and_replace_if_needed(item, nodes_being_cached) for item in value}

        return value

    return visit_and_replace_if_needed(root), replacement_info


@macro
def autocache(argument: AnyDensity, *, caching_function: DensityFunction = types.cache_once, max_nodes: int = 5) -> Density:
    """Optimizes a density function by automatically caching all recurring calculations.
    
    """
    wrapper = lambda value: Reference("rhombus:generated/" + uuid_hash(value.serialize_toplevel()), definition=caching_function(value))
    return Density(_wrap_redundances(argument.AST, max_nodes=max_nodes, wrapper=wrapper)[0])

def get_size(df: Density) -> DensityFunctionSizeInfo:
    """Returns information about the size of a density function.
    
    Returns:
        DensityFunctionSizeInfo
            - `~.nodes_uncached`: Number of nodes that are not part of a unique cached subtree
            - `~.nodes_in_unique_cached`: Number of nodes that are part of a unique cached subtree
            - `~.unique_unknown_references`: Number of unique references with unknown definition
            - `~.total_unknown_references`: Total number of references with unknown definition (counting duplicates)
    """
    # TODO evaluate how to count constants vs literals and references per se
    return _df_size_info(df.AST)