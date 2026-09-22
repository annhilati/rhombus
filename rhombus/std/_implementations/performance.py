from typing import NamedTuple, Any, Callable
import dataclasses
import sys

from beet.contrib import worldgen as beet_worldgen

from rhombus.core import RhombusASTNode, DensityFunction, Reference, JSON_hash,walk
from rhombus.std.density import Density
from rhombus.std.macros import resolve_ast_versioning
import rhombus.support.vanilla.types as vt

# Datapack density functions can have exceptionally deep ASTs (400+ nodes deep).
# We bump the recursion limit to prevent crashes during tree traversals and recursive hashing.
if sys.getrecursionlimit() < 10000:
    sys.setrecursionlimit(10000)


class DensityFunctionSizeInfo(NamedTuple):
    toplevel_nodes: int
    unique_cached_nodes: int
    unique_unknown_references: int
    total_unknown_references: int


def count_node_values(node: RhombusASTNode) -> dict[RhombusASTNode, int]:
    """Recursively count unique nodes.

    Nodes that are equal are grouped.
    """
    from rhombus.core.node import walk

    if not isinstance(node, RhombusASTNode):
        raise TypeError("Expected RhombusASTNode instance")

    counts: dict[RhombusASTNode, int] = {}
    for n in walk(node):
        counts[n] = counts.get(n, 0) + 1

    return counts


def df_size_info(node: DensityFunction) -> DensityFunctionSizeInfo:

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

    visit(Density.from_dict(files["rhombus:main"].data).AST)

    return DensityFunctionSizeInfo(
        toplevel_nodes=count_toplevel_nodes,
        unique_cached_nodes=count_unique_cached_nodes,
        unique_unknown_references=len(collect_unique_unknown_references),
        total_unknown_references=count_total_unknown_references,
    )


def cache_nodes(
    root: DensityFunction,
    *conditions: Callable[[DensityFunction, dict[RhombusASTNode, int]], bool],
    transformer: Callable[[DensityFunction], DensityFunction] = lambda df: Reference(
        "rhombus:partitioned/" + JSON_hash(df.serialize_toplevel()),
        definition=vt.cache(df),
    ),
) -> tuple[DensityFunction, dict[DensityFunction, int]]:
    occurrences = count_node_values(root)
    replacement_info: dict[DensityFunction, int] = {}

    def visit_and_replace_if_needed(
        value: DensityFunction | Any,
        nodes_being_cached: frozenset[DensityFunction] = frozenset(),
    ) -> DensityFunction | Any:
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
            optimized_value = dataclasses.replace(
                value,
                **{
                    field_name: visit_and_replace_if_needed(field_value, new_nodes_being_cached)
                    for field_name, field_value in value.fields.items()
                },
            )

            if should_cache:
                replacement_info[value] = replacement_info.get(value, 0) + 1
                return transformer(optimized_value)

            return optimized_value

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
