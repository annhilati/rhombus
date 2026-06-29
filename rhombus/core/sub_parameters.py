from typing import Self, ClassVar

from rhombus.core.utils import JSONDict, annotated_fields
from rhombus.core.node import RhombusASTNode
from rhombus.core.serializer import deserialize_any_inline, serialize_any_inline

__all__ = ["SubParameters"]

class SubParameters(RhombusASTNode):
    """The **`SubParameters`** base class implements functionality for nodes
    in the abstract syntax tree of Rhombus that simply represent a grouping
    of parameters. This is a concept very similar to Pythons `TypedDict` class.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/abstraction/)
    """

    fileclass: ClassVar[None] = None
      
    #======// Serialization //===================================================================//
      
    @classmethod
    def deserialize_toplevel(cls, data: JSONDict) -> Self:        
        fields = annotated_fields(cls)

        return cls(**{
            parameter: deserialize_any_inline(value, tp)
            for parameter, value in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
        })
    
    def serialize_toplevel(self) -> JSONDict:
        return {
            parameter: serialize_any_inline(value)
            for parameter, value
            in self.fields.items()
            if value is not None
        }