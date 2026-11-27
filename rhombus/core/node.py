__all__ = [
    "DatapackNode",
    "field",
    "FieldMeta",
    "walk",
    "transform",
    "get_known_datapack_types",
    "serialize_any_toplevel",
    "serialize_any_inline",
    "deserialize_any_toplevel",
    "deserialize_any_inline",
]


from typing import Self, Any, ClassVar, Callable, Union, TypeAliasType, Literal, ForwardRef, dataclass_transform, get_origin, get_args
from types import EllipsisType, UnionType
from functools import cached_property
from collections.abc import Iterator
import dataclasses
import inspect
import copy
import warnings
import builtins

from rhombus.core.utils import JSONValue, BeetFile, Annotation, fields, JSON_hash, check_type, annotated_fields
from rhombus.core.environment import RhombusEnvironment, DatapackVersion, VersionString, VersionTuple, get_module_extension_namespace, parse_version_specifier


@dataclasses.dataclass
class FieldMeta:
    added_with: DatapackVersion | VersionString | VersionTuple | EllipsisType = ...,
    removed_with: DatapackVersion | VersionString | VersionTuple | EllipsisType = ...,
    legacy_keys: dict[DatapackVersion | VersionString | VersionTuple, str] = dataclasses.field(default_factory=dict)
    legacy_types: dict[DatapackVersion | VersionString | VersionTuple, Annotation] = dataclasses.field(default_factory=dict)
    legacy_values: dict[DatapackVersion | VersionString | VersionTuple, Any] = dataclasses.field(default_factory=dict)
    validate: Callable[[Any], bool] | Callable[[Any, Any], bool] | None = None
    dependency_namespace: str = "datapack"

    def get_appropriate_key(self, env: RhombusEnvironment, default: str) -> str:
        for threshold, key in sorted(self.legacy_keys.items(), reverse=False):
            if env._check_version(threshold, namespace=self.dependency_namespace) is False:
                return key
        return default

    def get_appropriate_type(self, env: RhombusEnvironment, default: Annotation) -> Annotation:
        for threshold, typ in sorted(self.legacy_types.items(), reverse=False):
            if env._check_version(threshold, namespace=self.dependency_namespace) is False:
                return typ
        return default

    def is_present(self, env: RhombusEnvironment) -> bool:
        if self.added_with is not ... and env._check_version(self.added_with, namespace=self.dependency_namespace) is False:
            return False
        if self.removed_with is not ... and env._check_version(self.removed_with, namespace=self.dependency_namespace) is True:
            return False
        return True


def field[Node, Value](
    default: Value=...,
    *,
    added_with: DatapackVersion | VersionString | VersionTuple = ...,
    removed_with: DatapackVersion | VersionString | VersionTuple = ...,
    legacy_keys: dict[DatapackVersion | VersionString | VersionTuple, str] = {},
    legacy_types: dict[DatapackVersion | VersionString | VersionTuple, Annotation] = {},
    legacy_values: dict[DatapackVersion | VersionString | VersionTuple, Value] = {},
    validate: Callable[[Value], bool] | Callable[[Value, Node], bool] | None = None,
    **dataclass_field_kwargs
) -> dataclasses.Field:
    meta = FieldMeta(added_with=added_with, removed_with=removed_with, legacy_keys=legacy_keys, legacy_types=legacy_types, legacy_values=legacy_values, validate=validate)
    metadata = dataclass_field_kwargs.get("metadata", {})
    metadata["rhombus_meta"] = meta
    dataclass_field_kwargs["metadata"] = metadata
    
    if default is not ...:
        return dataclasses.field(default=default, **dataclass_field_kwargs)
    return dataclasses.field(**dataclass_field_kwargs)


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
        default_ns = get_module_extension_namespace(module_name) or "datapack"
        is_dp = (default_ns == "datapack")
        ns["__rhombus_namespace__"] = default_ns

        versions_kwarg = kwargs.pop("versions", None)
        if versions_kwarg is not None:
            if versions_kwarg is ...:
                versions_kwarg = (..., ...)
            elif isinstance(versions_kwarg, (int, float, str, tuple)) and not (isinstance(versions_kwarg, tuple) and len(versions_kwarg) == 2 and (versions_kwarg[1] is ... or isinstance(versions_kwarg[1], (int, float, str, tuple)))):
                versions_kwarg = (versions_kwarg, ...)
                
            parsed_versions = []
            for v in versions_kwarg:
                if v is not ... and v is not None:
                    parsed_versions.append(parse_version_specifier(v, interpret_as_game_version_convert_to_datapack_version=is_dp))
                else:
                    parsed_versions.append(...)
            ns["__rhombus_versions__"] = tuple(parsed_versions)        
        for field_name, field_obj in ns.items():
            if isinstance(field_obj, dataclasses.Field) and "rhombus_meta" in field_obj.metadata:
                meta: FieldMeta = field_obj.metadata["rhombus_meta"]
                meta.dependency_namespace = default_ns
                if meta.added_with is not ... and meta.added_with is not None:
                    meta.added_with = parse_version_specifier(meta.added_with, interpret_as_game_version_convert_to_datapack_version=is_dp)
                if meta.removed_with is not ... and meta.removed_with is not None:
                    meta.removed_with = parse_version_specifier(meta.removed_with, interpret_as_game_version_convert_to_datapack_version=is_dp)
                
                new_legacy_keys = {}
                for k, v in meta.legacy_keys.items():
                    k_norm = parse_version_specifier(k, interpret_as_game_version_convert_to_datapack_version=is_dp) if k is not ... else k
                    new_legacy_keys[k_norm] = v
                meta.legacy_keys = new_legacy_keys

                new_legacy_types = {}
                for k, v in meta.legacy_types.items():
                    k_norm = parse_version_specifier(k, interpret_as_game_version_convert_to_datapack_version=is_dp) if k is not ... else k
                    new_legacy_types[k_norm] = v
                meta.legacy_types = new_legacy_types
                
                new_legacy_values = {}
                for k, v in meta.legacy_values.items():
                    k_norm = parse_version_specifier(k, interpret_as_game_version_convert_to_datapack_version=is_dp) if k is not ... else k
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
            # Unwrap wrapper objects if they are passed in!
            if hasattr(value, "AST"):
                from rhombus.core.node import DatapackNode
                if isinstance(value.AST, DatapackNode):
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
                        from rhombus.core.models.density_function import DensityFunction
                        val = DensityFunction.deserialize_inline(val)
                    
                    if "rhombus_meta" in field.metadata:
                        meta: FieldMeta = field.metadata["rhombus_meta"]
                        
                        if val is not None and meta.validate is not None:
                            sig = inspect.signature(meta.validate)
                            if len(sig.parameters) == 1:
                                if not meta.validate(val):
                                    warnings.warn(f"Validation failed for field '{field.name}' with value {val!r}")
                            elif len(sig.parameters) == 2:
                                if not meta.validate(val, self):
                                    warnings.warn(f"Validation failed for field '{field.name}' with value {val!r} against node {self!r}")

                    # Type checking
                    hints = getattr(self.__class__, "__rhombus_type_hints__", None)
                    if hints is None:
                        hints = annotated_fields(self.__class__)
                        self.__class__.__rhombus_type_hints__ = hints

                    if field.name in hints:
                        expected_type = hints[field.name]
                        if "rhombus_meta" in field.metadata:
                            meta: FieldMeta = field.metadata["rhombus_meta"]
                            from rhombus.runtime import rho
                            expected_type = meta.get_appropriate_type(rho, expected_type)

                        from rhombus.core.abstract import RhombusASTNode
                        if not isinstance(val, RhombusASTNode) and not check_type(val, expected_type):
                            warnings.warn(f"Type mismatch in '{self.__class__.__name__}.{field.name}': Expected {expected_type}, got {type(val).__name__} ({val!r})")

                    # Freeze the node value (e.g. lists/dicts) to ensure immutability
                    object.__setattr__(self, field.name, _freeze_field_value(val))

        ns["__post_init__"] = __post_init__
        cls: DatapackNode = super().__new__(mcls, name, bases, ns)

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


class DatapackNode(metaclass=NodeDataclassTransformer, versions=(..., ...)):
    """The **`DatapackNode`** class defines the common behaviour for all nodes
    in the abstract syntax tree of datapack data.

    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/devs/abstraction/)
    """

    __dataclass_fields__:      ClassVar[dict[str, dataclasses.Field]]
    __dataclass_params__:      ClassVar[Any]
    __match_args__:            ClassVar[tuple[str, ...]]
    __rhombus_versions__:      ClassVar[tuple[DatapackVersion | VersionString | VersionTuple, DatapackVersion | VersionString | VersionTuple | EllipsisType] | None]
    __rhombus_namespace__:     ClassVar[str]
    __rhombus_legacy_values__: ClassVar[dict[str, dict[DatapackVersion | VersionString | VersionTuple, Any]]]
    __rhombus_fields__:        ClassVar[dict[str, FieldMeta]]
    
    _rhombus_frozen: ClassVar[bool]

    fileclass: ClassVar[type[BeetFile] | None]

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "Only subclasses of 'DatapackNode' can be instantiated directly, not 'DatapackNode' itself"
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
        if self is other:
            return True
        if isinstance(other, type(self)):
            return self.fields == other.fields
        return False

    def __hash__(self) -> int:
        h = getattr(self, "_cached_hash", None)
        if h is None:
            h = hash((self.__class__, tuple(self.fields.items())))
            object.__setattr__(self, "_cached_hash", h)
        return h

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
    def inscribed_toplevel_nodes(self) -> set["DatapackNode"]:
        """All nodes defined inside the abstract syntax tree of this node, that will
        require a separate file when compiling. This will include this node itself,
        if it always requires a separate file.
        """

        def _collect_inscribed_toplevel_nodes(value: Any) -> set["DatapackNode"]:
            nodes = set()
            if isinstance(value, DatapackNode):
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
        return f"rhombus:generated/{JSON_hash(self.serialize_toplevel())}"

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


# TODO: Get this clear
def get_known_datapack_types() -> dict[str, Any]:
    """Dynamically returns a mapping of built-in types and all subclasses of DatapackNode.

    This is used to dynamically resolve string annotations and forward references
    without hardcoding any specific domain or standard library types.
    """
    types_map: dict[str, Any] = {
        name: getattr(builtins, name)
        for name in dir(builtins)
        if isinstance(getattr(builtins, name), type)
    }
    types_map["None"] = type(None)
    types_map["Any"] = Any

    queue = [DatapackNode]
    while queue:
        curr = queue.pop(0)
        types_map[curr.__name__] = curr
        queue.extend(curr.__subclasses__())

    return types_map


# ======// Traversing //=========================================================================//

def walk(node: DatapackNode | Any) -> Iterator[DatapackNode]:
    """Yields all RhombusASTNodes in the tree recursively (top-down)."""

    if isinstance(node, DatapackNode):
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


def transform[T](node: DatapackNode | T, func: Callable[[DatapackNode], DatapackNode]) -> DatapackNode | T:
    """Traverses the AST and applies the given function to each RhombusASTNode.
    This creates a new tree if any child node is modified, while preserving nodes that are unchanged.
    """
    if isinstance(node, DatapackNode):
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


# ======// Serialization //======================================================================//

def serialize_any_toplevel[T](o: T) -> JSONValue:
    """Main serialization function for top-level values."""

    if isinstance(o, DatapackNode):
        return o.serialize_toplevel()

    # Correct me if I'm wrong but there aren't any other valid cases?
    raise NotImplementedError(
        "serialize_any_toplevel() was called with a value of a type that is not 'RhombusASTNode' "
        "This is unexpected and unknown how to handle."
    )


def serialize_any_inline[T](o: T) -> JSONValue:
    """Main serialization function for nested/inline values."""

    if isinstance(o, DatapackNode):
        return o.serialize_inline()

    elif isinstance(o, (list, set, tuple)):
        return list(serialize_any_inline(m) for m in o)

    elif isinstance(o, dict):
        return {serialize_any_inline(k): serialize_any_inline(v) for k, v in o.items()}

    return o  # Other JSONValues should be fine literally


def deserialize_any_toplevel[T](v: Any, t: type[T]) -> T:
    """Main deserialization function for top-level values."""
    return _deserialize_any(v, t, top_level=True)


def deserialize_any_inline[T](v: Any, t: type[T]) -> T:
    """Main deserialization function for nested/inline values."""
    return _deserialize_any(v, t, top_level=False)


def _deserialize_any[T](v: Any, t: type[T], *, top_level: bool) -> T:
    if isinstance(t, (str, ForwardRef)):
        type_str = t.__forward_arg__ if isinstance(t, ForwardRef) else t
        types_map = get_known_datapack_types()
        resolved = types_map.get(type_str)
        if resolved is None:
            try:
                resolved = eval(type_str, types_map)
            except Exception:
                resolved = None
        if resolved is not None:
            return _deserialize_any(v, resolved, top_level=top_level)

    origin = get_origin(t)

    if origin is None:
        if isinstance(t, TypeAliasType):
            return _deserialize_any(v, t.__value__, top_level=top_level)

        if isinstance(t, type):
            if issubclass(t, DatapackNode):
                if top_level:
                    return t.deserialize_toplevel(v)
                return t.deserialize_inline(v)

            if t is str:
                return str(v)
            if t is int:
                return int(v)
            if t is float:
                return float(v)
            if t is bool:
                return bool(v)
            if t is type(None):
                if v is None:
                    return None
                raise ValueError(f"Expected None, got {v!r}")

        if t is Any:
            return v

        raise ValueError(f"No deserialization procedure for target type '{t}' known")

    args = get_args(t)

    if origin is Literal:
        if v in args:
            return v
        raise ValueError(
            f"Value {v!r} is not one of the allowed Literal values {args!r}"
        )

    if origin in (list, set):
        inner_t = args[0] if len(args) == 1 else Union[*args]
        items = [_deserialize_any(m, inner_t, top_level=False) for m in v]
        return origin(items)

    if origin is tuple:
        if len(args) == 2 and args[1] is Ellipsis:
            inner_t = args[0]
            return tuple(_deserialize_any(m, inner_t, top_level=False) for m in v)
        return tuple(
            _deserialize_any(m, arg, top_level=False) for m, arg in zip(v, args)
        )

    if origin in (Union, UnionType):
        for arg in args:
            if arg is type(None) and v is None:
                return None
            if isinstance(arg, type) and isinstance(v, arg):
                try:
                    return _deserialize_any(v, arg, top_level=top_level)
                except Exception:
                    pass

        for arg in args:
            try:
                return _deserialize_any(v, arg, top_level=top_level)
            except Exception:
                continue

        raise ValueError(f"Cannot deserialize {v!r} into {t!r}")

    if origin is dict:
        kt, vt = args
        return {
            _deserialize_any(k, kt, top_level=False): _deserialize_any(
                val, vt, top_level=False
            )
            for k, val in v.items()
        }

    raise ValueError(f"No deserialization procedure for target type '{t}' known")
