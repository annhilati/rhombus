from typing import Self, Any
from rhombus.core.utils import JSONDict, fields, annotated_fields, BeetFileClass
from rhombus.core.node import Node, SerializationContext

__all__ = ["SubParameters"]


class SubParameters(Node):
    """Base class for parameter groups that are used inline in fields of density function types or another.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/extending/mod_support/sub_parameters/)
    """
      
    @classmethod
    def deserialize(cls, data: JSONDict, ctx: SerializationContext = SerializationContext.TOPLEVEL) -> Self:
        from rhombus.core.serializer import deserialize
        fields = annotated_fields(cls)

        return cls(**{
            parameter: deserialize(value, tp)
            for parameter, value in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
        })
    
    def serialize(self, ctx: SerializationContext = SerializationContext.TOPLEVEL) -> JSONDict:
        from rhombus.core.serializer import serialize
        return {**{
            parameter: serialize(value)
            for parameter, value
            in self.fields.items()
            if value is not None
        }}