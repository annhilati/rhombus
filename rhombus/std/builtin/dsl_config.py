__all__ = ["DSLConfig", "field"]


from dataclasses import dataclass, field
from typing import Any, dataclass_transform

_ = field()

@dataclass_transform()
class _DSLConfigMeta(type):
    def __new__(mcls, name: str, bases: tuple[type, ...], ns: dict[str, Any]) -> type:
        cls = super().__new__(mcls, name, bases, ns)
        return dataclass(cls)


# TODO: hashable
class DSLConfig(metaclass=_DSLConfigMeta):
    def build(self) -> Any:
        raise NotImplementedError