from dataclasses import dataclass, field
from typing import ClassVar, Self, Any
from beet.core.file import DataModelBase
from Rhombus.core.utils import JSONDict, uuid_hash, fields, annotated_fields

__all__ = ["DatapackResource", "BeetFileClass"]


type BeetFileClass = DataModelBase

@dataclass
class DatapackResource:
    """Abstract base class for resources that are provided by a datapack outside of a density function.
    
    [Rhombus Documentation Reference](https://annhilati.github.io/rhombus/extending/mod_support/datapack_resources/)
    """

    fileclass: ClassVar[type[BeetFileClass]]
    _reference: str | None = field(init=False, default=None)

    @property
    def _fields(self) -> dict[str, Any]:
        return fields(self)

    @property
    def identifier(self) -> str:
        "The identifier of the datapack resource including the namespace."
        if self._reference is not None:
            return self._reference if ":" in self._reference else "minecraft:" + self._reference
        return f"rhombus:generated/" + uuid_hash(self.encode())

    @identifier.setter
    def identifier(self, value: str | None) -> None:
        if not isinstance(value, str):
            raise TypeError(f"Cannot asign non-str value '{value} as reference identifier'")
        self._reference = value

    @classmethod
    def referenced(cls, identifier: str, /) -> Self:
        identifier = "minecraft:" + identifier if not ":" in identifier else identifier
        instance = cls(**{param: None for param in annotated_fields(cls)})
        instance.identifier = identifier
        return instance

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
        return {
            parameter: fEncode(value)
            for parameter, value in self._fields.items()
            if value is not None
        }

    def __eq__(self, other) -> bool: 
        return self.identifier == other.identifier
    
    def __hash__(self) -> int:
        return hash(uuid_hash(self.encode()))