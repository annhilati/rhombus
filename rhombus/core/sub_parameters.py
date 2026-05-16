from typing import Self

import beet

from rhombus.core.utils import JSONDict, annotated_fields, contextfunction, FROM_CONTEXT
from rhombus.core.node import RhombusASTNode, IGNORED
from rhombus.core.serializer import deserialize_any, serialize_any
from rhombus import config

__all__ = ["SubParameters"]


class SubParameters(RhombusASTNode):
    """Base class for parameter groups that are used inline in fields of density function types or another.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/extending/mod_support/sub_parameters/)
    """
      
    @classmethod
    @contextfunction(dp=config.ctx.datapack)
    def deserialize(cls, data: JSONDict, inline: bool = IGNORED, dp: beet.DataPack | None = FROM_CONTEXT) -> Self:        
        fields = annotated_fields(cls)

        return cls(**{
            parameter: deserialize_any(value, tp)
            for parameter, value in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
        })
    
    def serialize(self, inline: bool = IGNORED) -> JSONDict:
        return {**{
            parameter: serialize_any(value)
            for parameter, value
            in self.fields.items()
            if value is not None
        }}