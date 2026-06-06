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

    counts: dict[RhombusASTNode, int] = {}
    seen: set[int] = set()

    def increment(value: RhombusASTNode) -> None:
        for existing in counts:
            if existing == value:
                counts[existing] += 1
                return

        counts[value] = 1

    def visit(value: Any) -> None:
        if isinstance(value, RhombusASTNode):

            # Zyklen verhindern
            if id(value) in seen:
                return
            seen.add(id(value))

            increment(value)

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

                return # We do not want to count the references fields twice

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

class ReplacementInfo(NamedTuple):
    ...

# TODO    
def cache_redundances(root: DensityFunction, max_nodes: int = 10) -> tuple[DensityFunction, ReplacementInfo]:

    occurances = count_node_values(root)

    def visit_and_replace_if_needed(value: DensityFunction | Any) -> DensityFunction | Any:
        if isinstance(value, DensityFunction):

            if size(value).nodes_uncached > max_nodes:
                # Ersetze value durch eine Referenz
                ref_name = "rhombus:generated/" + uuid_hash(value.serialize_toplevel())
                reference = Reference(ref_name, definition=value)
                return reference

            for v in value.fields.values():
                return visit_and_replace_if_needed(v)

        elif isinstance(value, dict):
            for item in value.keys():
                return visit_and_replace_if_needed(item)
            for item in value.values():
                return visit_and_replace_if_needed(item)

        elif isinstance(value, (list, tuple, set)):
            for item in value:
                return visit_and_replace_if_needed(item)

    return visit_and_replace_if_needed(root), ReplacementInfo()