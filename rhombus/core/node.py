from typing import Self, Any, ClassVar, dataclass_transform
import dataclasses

from rhombus.core.utils import JSONValue, BeetFile, fields, uuid_hash

__all__ = ["RhombusASTNode"]
    

@dataclass_transform(field_specifiers=(dataclasses.Field, dataclasses.field))
class NodeDataclassTransformer(type):

    def __new__(mcls, name, bases, ns, **kwargs):
        cls = super().__new__(mcls, name, bases, ns)

        init = kwargs.pop("init", True)

        if init:
            cls = dataclasses.dataclass(
                cls,
                init=True,
                repr=False,
                eq=False
            )

        return cls

class RhombusASTNode(metaclass=NodeDataclassTransformer):
    "Base class for all nodes in a Rhombus AST"
  
    __dataclass_fields__: ClassVar[dict[str, dataclasses.Field[Any]]]
    __dataclass_params__: ClassVar[Any]
    __match_args__:       ClassVar[tuple[str, ...]]

    fileclass: ClassVar[type[BeetFile]]

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Base class RhombusASTNode cannot be instantiated directly. Please use a subclass with defined fields.")
               
    def __repr__(self) -> str:
        # The __repr__ function should generate a string that is a valid Rhombus expression, with which the data can be reconstructed 
        return self.__class__.__name__ + "(" + ", ".join([
            param + "=" + value.__repr__()
            for param, value
            in self.fields.items()
            if self.__dataclass_fields__[param].default != value
        ]) + ")"

    def __eq__(self, other) -> bool:
        if not isinstance(other, RhombusASTNode):
            return False
        return self.fields == other.fields
    
    def __hash__(self) -> int:
        return hash(uuid_hash(self.serialize_toplevel()))

        
    #======// Standard Implementations //========================================================//
    
    @property
    def fields(self) -> dict[str, Any]:
        "Standard implemenation for getting all parameters of the Node paired with their values"
        return fields(self)
    
    @property
    def inscribed_toplevel_nodes(self) -> set["RhombusASTNode"]:
        "Recursive search for all inscribed nodes, that will require a file when compiling"
        # TODO Idea: do not return files but Nodes
        nodes = set()
        for param, value in self.fields.items():
            if isinstance(value, RhombusASTNode):
                nodes |= value.inscribed_toplevel_nodes
        return nodes
        
        
    #======// Serialization //===================================================================//
    
    def serialize_toplevel(self) -> JSONValue:
        """Returns a JSON value containing the data serialized into the target
        format (usually a dict), like it would be used at the top of a file
        structure.

        For most node types, this will be the same as `~.serialize_toplevel`,
        but for nodes, that cannot be defined inline a reference is returned.
        Any default values for latter nodes are lost. To retrieve the data
        associated with the references, use `~.additional_described_files()`.
        """
        raise NotImplementedError(f"Class {self.__class__.__name__} is missing implementation of serialize_toplevel()")
    
    def serialize_inline(self):
        """Returns a JSON value containing the data serialized into the target
        format (usually a dict), like it would be used within a nested file
        structure.

        For most node types, this will be the same as `~.serialize_toplevel`,
        but for nodes, that cannot be defined inline a reference is returned.
        Any default values for latter nodes are lost. To retrieve the data
        associated with the references, use `~.additional_described_files()`.
        """
        return self.serialize_toplevel()
    
    @classmethod
    def deserialize_toplevel(cls, data: JSONValue) -> Self:
        """Creates an instance of the class from data like it would be found at
        the top of a file structure. 
        """
        raise NotImplementedError(f"Class {cls.__name__} is missing implementation of deserialize_toplevel()")
    
    @classmethod
    def deserialize_inline(cls, data: JSONValue):
        """Creates an instance of the class from data like it would be found
        within a nested file structure.
        """
        return cls.deserialize_toplevel(data)