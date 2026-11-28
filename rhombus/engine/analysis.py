__all__ = ["count_node_values", "df_size_info", "DensityFunctionComplexityInfo"]


from typing import NamedTuple, Any

from rhombus.core import DatapackNode, DensityFunction, Reference, walk
import rhombus.library.vanilla.types as vt

# TODO: Count octaves
# TODO: Add path-like nested number statistics
class DensityFunctionComplexityInfo(NamedTuple):
    toplevel_nodes: int
    unique_cached_nodes: int
    unique_unknown_references: int
    total_unknown_references: int


def count_node_values(node: DatapackNode) -> dict[DatapackNode, int]:
    """Recursively count unique nodes.

    Nodes that are equal are grouped.
    """

    if not isinstance(node, DatapackNode):
        raise TypeError("Expected RhombusASTNode instance")

    counts: dict[DatapackNode, int] = {}
    for n in walk(node):
        counts[n] = counts.get(n, 0) + 1

    return counts


def df_size_info(node: DensityFunction) -> DensityFunctionComplexityInfo:
    if not isinstance(node, DensityFunction):
        raise TypeError("Expected DensityFunction instance")

    count_toplevel_nodes: int = 0
    count_unique_cached_nodes: int = 0
    count_total_unknown_references: int = 0
    collect_unique_unknown_references: set[str] = set()

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

                collect_unique_unknown_references.add(value.identifier)
                count_total_unknown_references += 1
                return

            if isinstance(value, vt.cache):
                we_are_in_cached = True
            for child_node in value.fields.values():
                visit(child_node, we_are_in_cached=we_are_in_cached)

        elif isinstance(value, dict):
            for item in value.keys():
                visit(item, we_are_in_cached)
            for item in value.values():
                visit(item, we_are_in_cached)

        elif isinstance(value, (list, tuple, set, frozenset)):
            for item in value:
                visit(item, we_are_in_cached)

    root = node
    while isinstance(root, Reference) and root.identifier.startswith("rhombus:generated/") and root.definition is not None:
        root = root.definition
    visit(root, we_are_in_cached=False)

    return DensityFunctionComplexityInfo(
        toplevel_nodes=count_toplevel_nodes,
        unique_cached_nodes=count_unique_cached_nodes,
        unique_unknown_references=len(collect_unique_unknown_references),
        total_unknown_references=count_total_unknown_references,
    )
