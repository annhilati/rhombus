from typing import Self, Any, ClassVar, dataclass_transform, Callable
from types import EllipsisType
from functools import cached_property
import dataclasses
import copy

from rhombus.core.utils import JSONValue, BeetFile, fields, uuid_hash
from rhombus.core.environment import RhombusEnvironment, RhombusVersion, VersionLike

__all__ = ["RhombusASTNode", "field", "FieldMeta"]

@dataclasses.dataclass
class FieldMeta:
    added_with: VersionLike = 9.0,
    removed_with: VersionLike | EllipsisType = ...,
    legacy_keys: dict[VersionLike, str] = {},
    legacy_values: dict[VersionLike, Any] = {},
    validate: Callable[[Any], bool] | Callable[[Any, Any], bool] | None = None

    def is_active(self, env: RhombusEnvironment) -> bool:
        if env.check_version(self.added_with) is False:
            return False
        if env.check_version(self.removed_with) is True:
            return False
        return True

    def get_json_key(self, env: RhombusEnvironment, default: str) -> str:
        for threshold, key in sorted(self.legacy_keys.items(), reverse=False):
            if env.check_version(threshold) is False:
                return key
        return default

def field[Node, Value](
    default: Value=...,
    *,
    added_with: VersionLike = 9.0,
    removed_with: VersionLike = ...,
    legacy_keys: dict[VersionLike, str] = {},
    legacy_values: dict[VersionLike, Value] = {},
    validate: Callable[[Value], bool] | Callable[[Value, Node], bool] | None = None,
    **kwargs
) -> dataclasses.Field:
    meta = FieldMeta(added_with, removed_with, legacy_keys, legacy_values, validate)
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
        versions = kwargs.pop("versions", dataclasses.MISSING)
        
        legacy_values_map = {}
        annotations = ns.get("__annotations__", {})
        for name, annotation in annotations.items():
            if "ClassVar" in str(annotation):
                field_obj = ns.get(name)
                if isinstance(field_obj, dataclasses.Field) and "rhombus_meta" in field_obj.metadata:
                    meta: FieldMeta = field_obj.metadata["rhombus_meta"]
                    ns[name] = field_obj.default
                    if meta.legacy_values:
                        legacy_values_map[name] = meta.legacy_values

        user_post_init = ns.get("__post_init__")

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
                        from rhombus.core.environment import env
                        
                        # Only validate the field if it is currently active in the environment.
                        # Inactive fields are filled with None in __init__, which would fail validation here.
                        if meta.is_active(env) and meta.validate is not None:
                            import inspect
                            sig = inspect.signature(meta.validate)
                            if len(sig.parameters) == 1:
                                if not meta.validate(val):
                                    raise ValueError(f"Validation failed for field '{field.name}' with value {val!r}")
                            elif len(sig.parameters) == 2:
                                if not meta.validate(val, self):
                                    raise ValueError(f"Validation failed for field '{field.name}' with value {val!r} against node {self!r}")

                    # Freeze the node value (e.g. lists/dicts) to ensure immutability
                    object.__setattr__(
                        self,
                        field.name,
                        RhombusASTNode._freeze_field_value(val),
                    )

        ns["__post_init__"] = __post_init__
        cls = super().__new__(mcls, name, bases, ns)

        init = kwargs.pop("init", True)

        if init:
            cls = dataclasses.dataclass(cls, init=True, repr=False, eq=False)

            original_init = cls.__init__

            def __init__(self, *args, **kwargs):
                # Temporarily disable freezing so original_init can set attributes
                object.__setattr__(self, "_rhombus_frozen", False)
                
                from rhombus.core.environment import env
                all_fields = dataclasses.fields(self.__class__)
                active_fields: list[dataclasses.Field] = []
                
                # 1. Dynamically evaluate which fields are active in the current environment
                for f in all_fields:
                    if f.init:
                        if "rhombus_meta" in f.metadata:
                            meta: FieldMeta = f.metadata["rhombus_meta"]
                            if meta.is_active(env):
                                active_fields.append(f)
                        else:
                            active_fields.append(f)
                            
                active_positional = [f for f in active_fields if not getattr(f, 'kw_only', False)]
                
                # 2. Map provided positional arguments exclusively to ACTIVE fields
                if len(args) > len(active_positional):
                    raise TypeError(f"{self.__class__.__name__}.__init__() takes {len(active_positional)} positional arguments but {len(args)} were given")
                    
                new_kwargs = {}
                for i, arg in enumerate(args):
                    new_kwargs[active_positional[i].name] = arg
                    
                # 3. Process provided keyword arguments
                active_names = {f.name for f in active_fields}
                for k, v in kwargs.items():
                    if k not in active_names:
                        is_inactive = any(f.name == k for f in all_fields)
                        # If the field exists but is currently inactive, provide a specific error message
                        if is_inactive:
                            raise TypeError(f"{self.__class__.__name__}.__init__() got unexpected keyword argument '{k}' (field is inactive in this version)")
                        else:
                            raise TypeError(f"{self.__class__.__name__}.__init__() got an unexpected keyword argument '{k}'")
                    if k in new_kwargs:
                        raise TypeError(f"{self.__class__.__name__}.__init__() got multiple values for argument '{k}'")
                    new_kwargs[k] = v
                    
                # 4. Construct the final kwargs dict for the static original_init call
                final_kwargs = {}
                for f in all_fields:
                    if f.init:
                        if f.name in new_kwargs:
                            # Value was provided via args or kwargs
                            final_kwargs[f.name] = new_kwargs[f.name]
                        else:
                            # User did not provide the value. Check if it was required.
                            is_active = f in active_fields
                            has_default = (f.default is not dataclasses.MISSING) or (f.default_factory is not dataclasses.MISSING)
                            
                            if is_active and not has_default:
                                raise TypeError(f"{self.__class__.__name__}.__init__() missing required argument '{f.name}'")
                                
                            # If it is inactive or has a default, fill it in
                            if has_default:
                                final_kwargs[f.name] = f.default if f.default is not dataclasses.MISSING else f.default_factory()
                            else:
                                # Inactive arguments without a default are filled with None 
                                # to prevent the static dataclass __init__ from failing
                                final_kwargs[f.name] = None
                
                original_init(self, **final_kwargs)
                
                # Freeze the object again after initialization
                object.__setattr__(self, "_rhombus_frozen", True)

            cls.__init__ = __init__

        if versions is not dataclasses.MISSING:
            cls.__rhombus_versions__ = versions
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


class RhombusASTNode(metaclass=NodeDataclassTransformer, versions=(9.0, ...)):
    """The **`RhombusASTNode`** class defines the common behaviour for all nodes
    in the abstract syntax tree of Rhombus. It thus can be called the base class
    for all nodes.

    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/devs/abstraction/)
    """

    __dataclass_fields__: ClassVar[dict[str, dataclasses.Field]]
    __dataclass_params__: ClassVar[Any]
    __match_args__: ClassVar[tuple[str, ...]]
    __rhombus_versions__: ClassVar[tuple[VersionLike, VersionLike | EllipsisType] | None]
    __rhombus_legacy_values__: ClassVar[dict[str, dict[VersionLike, Any]]]
    __rhombus_fields__: ClassVar[dict[str, FieldMeta]]
    _rhombus_frozen: bool


    fileclass: ClassVar[type[BeetFile] | None]

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "Only subclasses of 'RhombusASTNode' can be instantiated directly, not 'RhombusASTNode' itself"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_rhombus_frozen", False) and name != "reference":
            raise dataclasses.FrozenInstanceError(f"cannot assign to field '{name}'")
        object.__setattr__(self, name, value)

    @staticmethod
    def _freeze_field_value(value: Any) -> Any:
        # Unwrap Density wrapper objects if they are passed in!
        from rhombus.std.density import Density
        if isinstance(value, Density):
            value = value.AST

        if isinstance(value, list):
            return tuple(RhombusASTNode._freeze_field_value(v) for v in value)
        if isinstance(value, tuple):
            return tuple(RhombusASTNode._freeze_field_value(v) for v in value)
        if isinstance(value, set):
            return frozenset(RhombusASTNode._freeze_field_value(v) for v in value)
        if isinstance(value, dict):
            return {
                RhombusASTNode._freeze_field_value(
                    k
                ): RhombusASTNode._freeze_field_value(v)
                for k, v in value.items()
            }
        return value

    def __repr__(self) -> str:
        return (
            self.__class__.__name__
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

    @classmethod
    def get_all_known_ids(cls) -> list[str]:
        if not hasattr(cls, "id"):
            return []
        ids = [cls.id]
        if hasattr(cls, "__rhombus_legacy_values__") and "id" in cls.__rhombus_legacy_values__:
            ids.extend(cls.__rhombus_legacy_values__["id"].values())
        return ids

    @classmethod
    def is_active(cls, env: RhombusEnvironment) -> bool:
        versions = getattr(cls, "__rhombus_versions__", None)
        if versions:
            added, removed = versions
            if added is not None and added is not ...:
                if env.check_version(added) is False:
                    return False
            if removed is not None and removed is not ...:
                if env.check_version(removed) is True:
                    return False
        return True

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

    # TODO: Should this be a field instead that gets automatically set on initialization?
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
            f"Class {self.__class__.__name__} is missing implementation of serialize_toplevel()"
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
