__all__ = ["RhombusASTNode", "field", "FieldMeta", "UnresolvedVersionedNode", "resolve_ast_versioning"]


from typing import Self, Any, ClassVar, Callable, dataclass_transform 
from types import EllipsisType
from functools import cached_property
from collections.abc import Iterator
import dataclasses
import inspect
import copy

from rhombus.core.utils import JSONValue, BeetFile, fields, uuid_hash
from rhombus.core.environment import RhombusEnvironment, DatapackVersion, VersionString, VersionTuple, _parse_version_specifier, get_module_addon_namespace, rho


@dataclasses.dataclass
class FieldMeta:
    added_with: DatapackVersion | VersionString | VersionTuple = ...,
    removed_with: DatapackVersion | VersionString | VersionTuple | EllipsisType = ...,
    legacy_keys: dict[DatapackVersion | VersionString | VersionTuple, str] = {},
    legacy_values: dict[DatapackVersion | VersionString | VersionTuple, Any] = {},
    validate: Callable[[Any], bool] | Callable[[Any, Any], bool] | None = None

    def get_appropriate_key(self, env: RhombusEnvironment, default: str) -> str:
        for threshold, key in sorted(self.legacy_keys.items(), reverse=False):
            if env._check_version(threshold) is False:
                return key
        return default


def field[Node, Value](
    default: Value=...,
    *,
    added_with: DatapackVersion | VersionString | VersionTuple = ...,
    removed_with: DatapackVersion | VersionString | VersionTuple = ...,
    legacy_keys: dict[DatapackVersion | VersionString | VersionTuple, str] = {},
    legacy_values: dict[DatapackVersion | VersionString | VersionTuple, Value] = {},
    validate: Callable[[Value], bool] | Callable[[Value, Node], bool] | None = None,
    **kwargs
) -> dataclasses.Field:
    meta = FieldMeta(added_with=added_with, removed_with=removed_with, legacy_keys=legacy_keys, legacy_values=legacy_values, validate=validate)
    metadata = kwargs.get("metadata", {})
    metadata["rhombus_meta"] = meta
    kwargs["metadata"] = metadata
    
    if default is not ...:
        return dataclasses.field(default=default, **kwargs)
    return dataclasses.field(**kwargs)


@dataclass_transform(field_specifiers=(dataclasses.Field, dataclasses.field))
class NodeDataclassTransformer(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        ns: dict[str, Any],
        **kwargs: Any
    ) -> type:
        module_name = ns.get("__module__", "")
        default_ns = get_module_addon_namespace(module_name) or "datapack"

        versions_kwarg = kwargs.pop("versions", None)
        if versions_kwarg is not None:
            if versions_kwarg is ...:
                versions_kwarg = (..., ...)
            elif isinstance(versions_kwarg, (int, float, str, tuple)) and not (isinstance(versions_kwarg, tuple) and len(versions_kwarg) == 2 and (versions_kwarg[1] is ... or isinstance(versions_kwarg[1], (int, float, str, tuple)))):
                versions_kwarg = (versions_kwarg, ...)
                
            parsed_versions = []
            for v in versions_kwarg:
                if v is not ... and v is not None:
                    parsed_versions.append(_parse_version_specifier(v, default_namespace=default_ns))
                else:
                    parsed_versions.append(...)
            ns["__rhombus_versions__"] = tuple(parsed_versions)        
        for field_name, field_obj in ns.items():
            if isinstance(field_obj, dataclasses.Field) and "rhombus_meta" in field_obj.metadata:
                meta: FieldMeta = field_obj.metadata["rhombus_meta"]
                if meta.added_with is not ... and meta.added_with is not None:
                    meta.added_with = _parse_version_specifier(meta.added_with, default_namespace=default_ns)
                if meta.removed_with is not ... and meta.removed_with is not None:
                    meta.removed_with = _parse_version_specifier(meta.removed_with, default_namespace=default_ns)
                
                new_legacy_keys = {}
                for k, v in meta.legacy_keys.items():
                    k_norm = _parse_version_specifier(k, default_namespace=default_ns) if k is not ... else k
                    new_legacy_keys[k_norm] = v
                meta.legacy_keys = new_legacy_keys
                
                new_legacy_values = {}
                for k, v in meta.legacy_values.items():
                    k_norm = _parse_version_specifier(k, default_namespace=default_ns) if k is not ... else k
                    new_legacy_values[k_norm] = v
                meta.legacy_values = new_legacy_values

        legacy_values_map = {}
        annotations = ns.get("__annotations__", {})
        for field_name, annotation in annotations.items():
            if "ClassVar" in str(annotation):
                field_obj = ns.get(field_name)
                if isinstance(field_obj, dataclasses.Field) and "rhombus_meta" in field_obj.metadata:
                    meta: FieldMeta = field_obj.metadata["rhombus_meta"]
                    ns[field_name] = field_obj.default
                    if meta.legacy_values:
                        legacy_values_map[field_name] = meta.legacy_values

        user_post_init = ns.get("__post_init__")
        
        def _freeze_field_value(value: Any) -> Any:
            # Unwrap Density wrapper objects if they are passed in!
            from rhombus.std.density import Density
            if isinstance(value, Density):
                value = value.AST

            if isinstance(value, list):
                return tuple(_freeze_field_value(v) for v in value)
            if isinstance(value, tuple):
                return tuple(_freeze_field_value(v) for v in value)
            if isinstance(value, set):
                return frozenset(_freeze_field_value(v) for v in value)
            if isinstance(value, dict):
                return {
                    _freeze_field_value(
                        k
                    ): _freeze_field_value(v)
                    for k, v in value.items()
                }
            return value

        def __post_init__(self):
            if user_post_init is not None:
                user_post_init(self)
            for field in dataclasses.fields(self):
                if field.init:
                    val = getattr(self, field.name)
                    
                    # Automatically deserialize inline-declared DensityFunctions
                    if isinstance(val, (int, float, str)) and "DensityFunction" in str(field.type):
                        from rhombus.core.density_function import DensityFunction
                        val = DensityFunction.deserialize_inline(val)
                    
                    if "rhombus_meta" in field.metadata:
                        meta: FieldMeta = field.metadata["rhombus_meta"]
                        
                        if val is not None and meta.validate is not None:
                            import inspect
                            sig = inspect.signature(meta.validate)
                            if len(sig.parameters) == 1:
                                if not meta.validate(val):
                                    raise ValueError(f"Validation failed for field '{field.name}' with value {val!r}")
                            elif len(sig.parameters) == 2:
                                if not meta.validate(val, self):
                                    raise ValueError(f"Validation failed for field '{field.name}' with value {val!r} against node {self!r}")

                    # Freeze the node value (e.g. lists/dicts) to ensure immutability
                    object.__setattr__(self, field.name, _freeze_field_value(val))

        ns["__post_init__"] = __post_init__
        cls = super().__new__(mcls, name, bases, ns)

        init = kwargs.pop("init", True)

        if init:
            cls = dataclasses.dataclass(cls, init=True, repr=False, eq=False)

            original_init = cls.__init__
            
            sig = inspect.signature(original_init)

            def __init__(self, *args, **kwargs):
                bound = sig.bind_partial(self, *args, **kwargs)
                bound.apply_defaults()
                
                final_kwargs = bound.arguments
                final_kwargs.pop("self", None)
                
                # Fill missing arguments with None so original_init doesn't crash
                for param_name in list(sig.parameters.keys())[1:]:
                    if param_name not in final_kwargs:
                        final_kwargs[param_name] = None
                
                # Temporarily disable freezing so original_init can set attributes
                object.__setattr__(self, "_rhombus_frozen", False)
                
                original_init(self, **final_kwargs)
                
                # Freeze the object again after initialization
                object.__setattr__(self, "_rhombus_frozen", True)

            cls.__init__ = __init__


        cls.__rhombus_legacy_values__ = legacy_values_map
        
        rhombus_fields = {}
        try:
            for f in dataclasses.fields(cls):
                if "rhombus_meta" in f.metadata:
                    rhombus_fields[f.name] = f.metadata["rhombus_meta"]
        except TypeError:
            pass
        cls.__rhombus_fields__ = rhombus_fields

        return cls


class RhombusASTNode(metaclass=NodeDataclassTransformer, versions=(..., ...)):
    """The **`RhombusASTNode`** class defines the common behaviour for all nodes
    in the abstract syntax tree of Rhombus. It thus can be called the base class
    for all nodes.

    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/devs/abstraction/)
    """

    __dataclass_fields__: ClassVar[dict[str, dataclasses.Field]]
    __dataclass_params__: ClassVar[Any]
    __match_args__: ClassVar[tuple[str, ...]]
    __rhombus_versions__: ClassVar[tuple[DatapackVersion | VersionString | VersionTuple, DatapackVersion | VersionString | VersionTuple | EllipsisType] | None]
    __rhombus_legacy_values__: ClassVar[dict[str, dict[DatapackVersion | VersionString | VersionTuple, Any]]]
    __rhombus_fields__: ClassVar[dict[str, FieldMeta]]
    _rhombus_frozen: ClassVar[bool]

    fileclass: ClassVar[type[BeetFile] | None]

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "Only subclasses of 'RhombusASTNode' can be instantiated directly, not 'RhombusASTNode' itself"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_rhombus_frozen", False) and name != "reference":
            raise dataclasses.FrozenInstanceError(f"cannot assign to field '{name}'")
        object.__setattr__(self, name, value)
   

    def __repr__(self) -> str:
        return (
            type(self).__name__
            + "("
            + ", ".join(
                [
                    param + "=" + value.__repr__()
                    for param, value in self.fields.items()
                    if self.__dataclass_fields__[param].default != value
                ]
            )
            + ")"
        )

    def __eq__(self, other) -> bool:
        if type(self) is not type(other):
            return False
        return self.fields == other.fields

    def __hash__(self) -> int:
        return hash(self.identifier)

    def __copy__(self) -> Self:
        return self.__class__(**self.fields)

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        new_fields = {
            name: copy.deepcopy(value, memo) for name, value in self.fields.items()
        }
        return self.__class__(**new_fields)

    @property
    def fields(self) -> dict[str, Any]:
        "The fields of this node as a dictionary."
        return fields(self)


    # ======// Serialization //===================================================================//

    @property
    def inscribed_toplevel_nodes(self) -> set["RhombusASTNode"]:
        """All nodes defined inside the abstract syntax tree of this node, that will
        require a separate file when compiling. This will include this node itself,
        if it always requires a separate file.
        """

        def _collect_inscribed_toplevel_nodes(value: Any) -> set["RhombusASTNode"]:
            nodes = set()
            if isinstance(value, RhombusASTNode):
                nodes |= value.inscribed_toplevel_nodes
            elif isinstance(value, dict):
                for key, item in value.items():
                    nodes |= _collect_inscribed_toplevel_nodes(key)
                    nodes |= _collect_inscribed_toplevel_nodes(item)
            elif isinstance(value, (list, tuple, set, frozenset)):
                for item in value:
                    nodes |= _collect_inscribed_toplevel_nodes(item)
            return nodes

        nodes = set()
        for value in self.fields.values():
            nodes |= _collect_inscribed_toplevel_nodes(value)
        return nodes

    # IDEA: Should this be a field instead that gets automatically set on initialization?
    @cached_property
    def identifier(self) -> str:
        """The namespaced resource identifier of this node. This can be a fixed
        string or one generated from the nodes data.
        """
        return f"rhombus:generated/{uuid_hash(self.serialize_toplevel())}"

    def serialize_toplevel(self) -> JSONValue:
        """Serializes the nodes data into the target format (usually a JSON
        dictionary), like it would be used at the top of a file structure.
        """
        raise NotImplementedError(
            f"Class {type(self).__name__} is missing implementation of serialize_toplevel()"
        )

    def serialize_inline(self):
        """Serializes the nodes data into the target format (usually a JSON
        dictionary), like it would be used within a nested file structure.

        For most node types, this will be the same as `~.serialize_toplevel()`,
        but for nodes, that cannot be defined inline a reference is returned.
        Any default values for latter nodes are lost. To retrieve the data
        associated with the reference, use `~.inscribed_toplevel_nodes`.
        """
        return self.serialize_toplevel()

    @classmethod
    def deserialize_toplevel(cls, data: JSONValue) -> Self:
        """Creates an instance of this node class from data (usually a JSON
        dictionary) like it would be found at the top of a file structure.
        """
        raise NotImplementedError(
            f"Class {cls.__name__} is missing implementation of deserialize_toplevel()"
        )

    @classmethod
    def deserialize_inline(cls, data: JSONValue):
        """Creates an instance of this node class from data (usually a JSON
        dictionary) like it would be found within a nested file structure.
        """
        return cls.deserialize_toplevel(data)


class UnresolvedVersionedNode(RhombusASTNode):
    dispatcher: Callable = dataclasses.field(repr=False, compare=False)
    args: tuple[Any, ...] = dataclasses.field(repr=False, compare=False)
    kwargs: dict[str, Any] = dataclasses.field(repr=False, compare=False)
    repr_func: Callable[["UnresolvedVersionedNode"], str] | None = dataclasses.field(
        default=None, repr=False, compare=False
    )

    _cached_version: Any = dataclasses.field(init=False, default=None, repr=False, compare=False)
    _cached_node: RhombusASTNode | None = dataclasses.field(
        init=False, default=None, repr=False, compare=False
    )

    def __repr__(self) -> str:
        if self.repr_func is not None:
            return self.repr_func(self)
        parts = [repr(arg) for arg in self.args]
        parts.extend(f"{k}={repr(v)}" for k, v in self.kwargs.items())
        return f"{self.dispatcher.__name__}({', '.join(parts)})"

    def resolve(self) -> RhombusASTNode:
        from rhombus.std.density import Density
        # TODO: Is this only for Density? Should be generic
        
        current_version = rho.datapack_version

        if self._cached_version == current_version and self._cached_node is not None:
            return self._cached_node

        result = self.dispatcher._execute_for_version(*self.args, **self.kwargs) # type: ignore
        object.__setattr__(self, "_cached_version", current_version)

        if isinstance(result, Density):
            object.__setattr__(self, "_cached_node", result.AST)
        elif isinstance(result, RhombusASTNode):
            object.__setattr__(self, "_cached_node", result)
        else:
            raise TypeError(
                f"Version node dispatcher returned invalid type: {type(result)}"
            )

        return self._cached_node

    # Pass through standard methods to the resolved node
    def serialize_inline(self):
        return self.resolve().serialize_inline()

    def serialize_toplevel(self):
        return self.resolve().serialize_toplevel()

    @property
    def inscribed_toplevel_nodes(self) -> set[RhombusASTNode]:
        return self.resolve().inscribed_toplevel_nodes


def walk(node: RhombusASTNode | Any) -> Iterator[RhombusASTNode]:
    """Yields all RhombusASTNodes in the tree recursively (top-down)."""

    if isinstance(node, RhombusASTNode):
        yield node
        for value in node.fields.values():
            yield from walk(value)
    elif isinstance(node, (list, tuple, set, frozenset)):
        for item in node:
            yield from walk(item)
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk(k)
            yield from walk(v)


def transform(node: RhombusASTNode | Any, func: Callable[[RhombusASTNode], RhombusASTNode]) -> Any:
    """Traverses the AST and applies the given function to each RhombusASTNode.
    This creates a new tree if any child node is modified, while preserving nodes that are unchanged.
    """
    if isinstance(node, RhombusASTNode):
        changes = {}
        for field_name, child_value in node.fields.items():
            new_child_value = transform(child_value, func)
            if new_child_value is not child_value:
                changes[field_name] = new_child_value

        if changes:
            # Create a new instance with the transformed children
            new_node = copy.copy(node)
            object.__setattr__(new_node, "_rhombus_frozen", False)
            for k, v in changes.items():
                object.__setattr__(new_node, k, v)
            object.__setattr__(new_node, "_rhombus_frozen", True)
            node = new_node
            
        return func(node)

    elif isinstance(node, list):
        new_list = [transform(item, func) for item in node]
        return new_list if new_list != node else node

    elif isinstance(node, tuple):
        new_tuple = tuple(transform(item, func) for item in node)
        return new_tuple if new_tuple != node else node
        
    elif isinstance(node, set):
        new_set = {transform(item, func) for item in node}
        return new_set if new_set != node else node
        
    elif isinstance(node, frozenset):
        new_frozenset = frozenset(transform(item, func) for item in node)
        return new_frozenset if new_frozenset != node else node

    elif isinstance(node, dict):
        new_dict = {transform(k, func): transform(v, func) for k, v in node.items()}
        return new_dict if new_dict != node else node

    return node


def resolve_ast_versioning(node: RhombusASTNode) -> RhombusASTNode:
    """Recursively traverses the AST and resolves all UnresolvedVersionedNodes."""
    
    def _resolver(n: RhombusASTNode) -> RhombusASTNode:
        if isinstance(n, UnresolvedVersionedNode):
            # Since UnresolvedVersionedNode might return a node that itself needs resolving/transforming,
            # we need to transform the newly resolved branch as well.
            return resolve_ast_versioning(n.resolve())
        return n

    return transform(node, _resolver)

