from typing import Self, Any, ClassVar, dataclass_transform
import dataclasses
import copy
from functools import cached_property

from rhombus.core.utils import JSONValue, BeetFile, fields, uuid_hash

__all__ = ["RhombusASTNode"]


@dataclass_transform(field_specifiers=(dataclasses.Field, dataclasses.field))
class NodeDataclassTransformer(type):
    def __new__(mcls, name, bases, ns, **kwargs):
        user_post_init = ns.get("__post_init__")

        def __post_init__(self):
            if user_post_init is not None:
                user_post_init(self)
            for field in dataclasses.fields(self):
                if field.init:
                    object.__setattr__(
                        self,
                        field.name,
                        RhombusASTNode._freeze_field_value(getattr(self, field.name)),
                    )

        ns["__post_init__"] = __post_init__
        cls = super().__new__(mcls, name, bases, ns)

        init = kwargs.pop("init", True)

        if init:
            cls = dataclasses.dataclass(cls, init=True, repr=False, eq=False)

            original_init = cls.__init__

            def __init__(self, *args, **kwargs):
                object.__setattr__(self, "_rhombus_frozen", False)
                original_init(self, *args, **kwargs)
                object.__setattr__(self, "_rhombus_frozen", True)

            cls.__init__ = __init__

        return cls


class RhombusASTNode(metaclass=NodeDataclassTransformer):
    """The **`RhombusASTNode`** class defines the common behaviour for all nodes
    in the abstract syntax tree of Rhombus. It thus can be called the base class
    for all nodes.

    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/devs/abstraction/)
    """

    __dataclass_fields__: ClassVar[dict[str, dataclasses.Field[Any]]]
    __dataclass_params__: ClassVar[Any]
    __match_args__: ClassVar[tuple[str, ...]]

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
