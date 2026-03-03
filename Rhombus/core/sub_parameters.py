from typing import Any, Self

from Rhombus.core.utils import JSONDict, fields, annotated_fields

class SubParameters:
    """Base class for parameter groups that are used inline in fields of density function types or another.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/extending/mod_support/sub_parameters/)
    """

    @property
    def fields(self) -> dict[str, Any]:
        "Returns the fields of the sub parameters, with their values."
        return fields(self)
    
    @classmethod
    def decode(cls, data: JSONDict) -> Self:
        from Rhombus.core.codec import fDecode
        fields = annotated_fields(cls)

        return cls(**{
            parameter: fDecode(value, tp)
            for parameter, value in data.items()
            if parameter in fields
            for tp in (fields[parameter],)
        })
    
    def encode(self) -> JSONDict:
        from Rhombus.core.codec import fEncode
        return {**{
            parameter: fEncode(value)
            for parameter, value
            in self.fields.items()
            if value is not None
        }}