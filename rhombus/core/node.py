from typing import Self, Any
from dataclasses import dataclass

from rhombus.core.utils import JSONValue, BeetFile, fields

__all__ = ["RhombusASTNode"]
    
@dataclass
class RhombusASTNode:
    "Base class for all nodes in a Rhombus AST"
    
    def __init_subclass__(cls, **kwargs):   
        super().__init_subclass__(**kwargs)
               
    def __repr__(self) -> str:
        # Philosophy:
        # The __repr__ function should generate a string that is a valid Rhombus expression, with which the data can be reconstructed 
        return self.__class__.__name__ + "(" + ", ".join([
            param + "=" + value.__repr__()
            for param, value
            in self.fields.items()
            if self.__dataclass_fields__[param].default != value
        ]) + ")"

        
    #======// Standard Implementations //========================================================//
    
    @property
    def fields(self) -> dict[str, Any]:
        "Standard implemenation for getting all parameters of the Node paired with their values."
        return fields(self)
    
    def additional_described_files(self) -> dict[str, BeetFile]:
        "Standard implementation for recursive search for additional files. Returns all files of all entries in `~.fields`."
        # Additionaly and excluding the one with the content of ~.serialize()
        files = {}
        for param, value in self.fields.items():
            if isinstance(value, RhombusASTNode):
                files |= value.additional_described_files()
        return files
        
        
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
        raise NotImplementedError
    
    def serialize_inline(self) -> JSONValue:
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
    def deserialize_toplevel(cls, data) -> Self:
        """Creates an instance of the class from data like it would be found at
        the top of a file structure. 
        """
        raise NotImplementedError
    
    @classmethod
    def deserialize_inline(cls, data) -> Self:
        """Creates an instance of the class from data like it would be found
        within a nested file structure.
        """
        return cls.deserialize_toplevel(data=data)