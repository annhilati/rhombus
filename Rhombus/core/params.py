from typing import Any, Self

from Rhombus.core.utils import JSONDict, fields, annotated_fields
from Rhombus.core.codec import encode as uniencode, decode as unidecode

class SubParameters:
    """Base class for parameter groups that are used inline in fields of density function types or another.
    
    """

    @property
    def fields(self) -> dict[str, Any]:
        "Returns the fields of the sub parameters, with their values."
        return fields(self)
    
    @classmethod
    def decode(cls, data: JSONDict) -> Self:
        fields = annotated_fields(cls)

        return cls(**{
            parameter: unidecode(value, tp)
            for parameter, value in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
        })
    
    def encode(self) -> JSONDict:
        return {**{
            parameter: uniencode(value)
            for parameter, value
            in self.fields.items()
            if value is not None
        }}