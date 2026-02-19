from typing import Any, Self, get_type_hints
from dataclasses import fields

from Rhombus.core import JSONDict

class SubParameters:

    @property
    def fields(self) -> dict[str, Any]:
        "Returns the fields of the sub parameter with their values."
        return {
            f.name: getattr(self, f.name, None)
            for f in fields(self)
            if f.init
        }
    
    @classmethod
    def decode(cls, data: JSONDict) -> Self:
        init_fields: dict[str, type] = {
            f.name: get_type_hints(cls)[f.name]
            for f in fields(cls)
            if f.init
        }

        return cls(**{
            parameter: (
                ... if False
                
                else value
            )
            for parameter, value in data.items()
            if parameter in init_fields
            for tp in (init_fields[parameter],)
        })
    
    def encode(self) -> JSONDict:
        return {**{
            parameter: (
                ... if False
                    
                else value)
            for parameter, value
            in self.fields.items()
        }}