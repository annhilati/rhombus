from rhombus.core import RhombusASTNode
import anytree
import json
from typing import NamedTuple, Any
from rhombus.core.utils import uuid_hash
from rhombus.core.density_function import DensityFunction, Reference
from rhombus.std import types
import copy

def count_nodes(node: RhombusASTNode) -> dict[type[RhombusASTNode], int]:
    """Recursively counts RhombusASTNode instances by the direct RhombusASTNode subclass type.

    Nodes whose class is a subclass of a direct RhombusASTNode descendant are
    counted as that direct descendant, not separately.
    """
    if not isinstance(node, RhombusASTNode):
        raise TypeError("Expected RhombusASTNode instance")

    counts: dict[type[RhombusASTNode], int] = {}
    seen: set[int] = set()

    def direct_rhombus_type(value: RhombusASTNode) -> type[RhombusASTNode]:
        cls = type(value)
        if RhombusASTNode in cls.__bases__:
            return cls
        for base in cls.__mro__[1:]:
            if RhombusASTNode in base.__bases__:
                return base
        return cls

    def visit(value: Any) -> None:
        if isinstance(value, RhombusASTNode):
            if id(value) in seen:
                return
            seen.add(id(value))
            direct_type = direct_rhombus_type(value)
            counts[direct_type] = counts.get(direct_type, 0) + 1
            for child in value.fields.values():
                visit(child)
        elif isinstance(value, dict):
            for item in value.keys():
                visit(item)
            for item in value.values():
                visit(item)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                visit(item)

    visit(node)
    return counts

def count_node_values(node: RhombusASTNode) -> dict[RhombusASTNode, int]:
    """Recursively count unique nodes.

    Nodes that are equal are grouped.
    """

    if not isinstance(node, RhombusASTNode):
        raise TypeError("Expected RhombusASTNode instance")
    # Use a stable serialized representation as grouping key to avoid
    # relying on object identity or potentially brittle equality semantics.
    import json

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

def collect_references(node: RhombusASTNode) -> list[Reference]:
    """Gibt alle Reference-Instanzen im Baum zurück."""

    if not isinstance(node, RhombusASTNode):
        raise TypeError("Expected RhombusASTNode instance")

    references: list[Reference] = []
    seen: set[int] = set()
    seen_references: set = set()

    def visit(value: Any) -> None:
        if isinstance(value, RhombusASTNode):
            if id(value) in seen:
                return
            seen.add(id(value))

            if isinstance(value, Reference):
                # avoid returning duplicate logical references
                key = getattr(value, "reference", None) or id(value)
                if key not in seen_references:
                    seen_references.add(key)
                    references.append(value)

            for child in value.fields.values():
                visit(child)

        elif isinstance(value, dict):
            for item in value.keys():
                visit(item)
            for item in value.values():
                visit(item)

        elif isinstance(value, (list, tuple, set)):
            for item in value:
                visit(item)

    visit(node)
    return references



def build_reference_tree(
    root: RhombusASTNode,
    root_name: str,
) -> anytree.Node:
    if not isinstance(root, RhombusASTNode):
        raise TypeError("Expected RhombusASTNode instance")

    def is_reference(value: Any) -> bool:
        return isinstance(value, Reference)

    def collect_references_deep(value: Any, out: list[Reference], seen_ids: set[int]) -> None:
        """Sammelt alle Reference-Instanzen tief in einem Wert.

        Sobald eine Reference gefunden wird, wird sie aufgenommen und nicht
        weiter in ihre eigenen Felder hinabgestiegen.
        """
        if isinstance(value, RhombusASTNode):
            if id(value) in seen_ids:
                return
            seen_ids.add(id(value))

            if is_reference(value):
                out.append(value)
                return

            for child in value.fields.values():
                collect_references_deep(child, out, seen_ids)

        elif isinstance(value, dict):
            for item in value.keys():
                collect_references_deep(item, out, seen_ids)
            for item in value.values():
                collect_references_deep(item, out, seen_ids)

        elif isinstance(value, (list, tuple, set)):
            for item in value:
                collect_references_deep(item, out, seen_ids)

    def dependencies_of_reference(reference: Reference) -> list[Reference]:
        """Alle Reference-Abhängigkeiten, die in dieser Reference stecken."""
        deps: list[Reference] = []
        seen_ids: set[int] = set()

        for child in reference.fields.values():
            collect_references_deep(child, deps, seen_ids)

        return deps

    def top_level_references(ast: RhombusASTNode) -> list[Reference]:
        """Alle References, die direkt oder verschachtelt im AST vorkommen."""
        refs: list[Reference] = []
        seen_ids: set[int] = set()
        for value in ast.fields.values():
            collect_references_deep(value, refs, seen_ids)
        return refs

    def build_node(
        reference: Reference,
        parent: anytree.Node,
        path: set[str],
    ) -> None:
        name = str(reference.reference)

        if name in path:
            return

        node = anytree.Node(name, parent=parent, reference=reference)

        next_path = set(path)
        next_path.add(name)

        seen_children: set[str] = set()
        for child_ref in dependencies_of_reference(reference):
            child_name = str(child_ref.reference)

            if child_name in seen_children:
                continue
            if child_name in next_path:
                continue

            seen_children.add(child_name)
            build_node(child_ref, node, next_path)

    tree_root = anytree.Node(root_name)

    seen_root_children: set[str] = set()
    for ref in top_level_references(root):
        name = str(ref.reference)
        if name in seen_root_children:
            continue
        seen_root_children.add(name)
        build_node(ref, tree_root, {root_name})

    return tree_root


class DensityFunctionSizeInfo(NamedTuple):
    nodes_uncached: int
    nodes_in_unique_cached: int
    unique_unknown_references: int
    total_unknown_references: int

def size(node: DensityFunction) -> DensityFunctionSizeInfo:
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

# TODO    
def cache_redundances(root: DensityFunction, max_nodes: int = 10) -> tuple[DensityFunction, dict[DensityFunction, int]]:
    """Returns `root` but replaces all sub trees that occur multilpe times and have a size
    of more than `max_nodes` uncached nodes with partitioned and cached versions.
    """

    occurances = count_node_values(root)
    replacement_info: dict[DensityFunction, int] = {}

    def clone_node(node: DensityFunction) -> DensityFunction:
        return node.__class__(**{
            field_name: field_value
            for field_name, field_value in node.fields.items()
        })

    def visit_and_replace_if_needed(value: DensityFunction | Any) -> DensityFunction | Any:
        if isinstance(value, DensityFunction):

            if occurances[value] > 1 and size(value).nodes_uncached > max_nodes:
                # Optimize children first before caching
                optimized = clone_node(value)
                for field_name, field_value in value.fields.items():
                    new_value = visit_and_replace_if_needed(field_value)
                    setattr(optimized, field_name, new_value)
                
                # Wrap optimized content in cache_once and reference
                ref_name = "rhombus:generated/" + uuid_hash(optimized.serialize_toplevel())
                reference = Reference(ref_name, definition=types.cache_once(optimized))
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