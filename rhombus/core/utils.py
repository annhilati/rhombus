__all__ = [
    "JSONValue",
    "JSONDict",
    "BeetFile",
    "Annotation",
    "Decorator",
    "Dataclass",
    "DataclassInstance",
    "uuid_hash",
    "fields",
    "annotated_fields",
    "GlobalBinding",
    "get_Minecraft_datapack_version"
]

from typing import Callable, Any, get_type_hints
import hashlib
import uuid
import json
import dataclasses
import contextvars
import urllib.request

import beet
import beet.library.base


# ======// Typing //==============================================================================//

type JSONValue = (
    dict[str, JSONValue]
    | list[JSONValue]
    | tuple[JSONValue]
    | str
    | int
    | float
    | bool
    | None
)
type JSONDict = dict[str, JSONValue]


class BeetFile(beet.library.base.NamespaceFile):
    """The **`BeetFile`** protocol is an extension of Beets `NamespaceFile`
    protocol to include attributes and methods that are important for encoding.
    Note that both are not runtime checkable.
    """

    data: JSONDict
    encoder: Callable[[JSONDict], str]
    decoder: Callable[[str], JSONDict]


type Annotation = type
type Decorator[**P, T] = Callable[[Callable[P, T]], Callable[P, T]]
type Dataclass = type
type DataclassInstance = object


# ======// Data //================================================================================//


def uuid_hash(data: JSONDict) -> str:
    """Creates a UUID string without dashes based of a JSON dictionary."""
    encoded_str = json.dumps(
        data, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("utf-8")
    hash_digest = hashlib.sha256(encoded_str).digest()
    return str(uuid.UUID(bytes=hash_digest[:16])).replace("-", "")


# ======// Dataclasses //=========================================================================//


def fields(o: DataclassInstance) -> dict[str, Any]:
    "Returns the fields of a dataclass instance, that are present in the init, with their values."
    try:
        flds = dataclasses.fields(o)
    except TypeError:
        raise TypeError(f"must be called with a dataclass instance, not: {o}")
    return dict(
        sorted({f.name: getattr(o, f.name, None) for f in flds if f.init}.items())
    )


def annotated_fields(o: Dataclass) -> dict[str, Annotation]:
    "Returns the fields of a dataclass, that are present in the init, with their annotation."
    try:
        flds = dataclasses.fields(o)
    except TypeError:
        raise TypeError(f"must be called with a dataclass type or instance, not: {o}")
    return {f.name: get_type_hints(o)[f.name] for f in flds if f.init}


# ======// Global Bindings //=====================================================================//


class GlobalBinding[T]:
    """Provide a directly usable global object for any class instance.

    The underlying instance is created lazily and stays bound to the current
    context. The proxy makes it feel like a plain global object while leaving
    the target class reusable in ordinary code.
    """

    def __init__(self, factory: Callable[[], T]) -> None:
        self._factory = factory
        self._ctxvar: contextvars.ContextVar[T | None] = contextvars.ContextVar(
            f"{factory.__name__}_binding", default=None
        )

    def _get_instance(self) -> T:
        instance = self._ctxvar.get()
        if instance is None:
            instance = self._factory()
            self._ctxvar.set(instance)
        return instance

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_instance(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            setattr(self._get_instance(), name, value)

    def __getattribute__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            return getattr(self._get_instance(), name)
        return object.__getattribute__(self, name)

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        return self._get_instance()(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        _DELEGATED_METHODS = {
            "__call__",
            "__getitem__",
            "__setitem__",
            "__iter__",
            "__len__",
            "__contains__",
            "__bool__",
            "__eq__",
            "__lt__",
            "__le__",
            "__gt__",
            "__ge__",
            "__add__",
            "__sub__",
            "__mul__",
            "__truediv__",
            "__radd__",
            "__rsub__",
            "__rmul__",
            "__rtruediv__",
        }
        value = getattr(self._get_instance(), name)
        if name in _DELEGATED_METHODS:
            return lambda *args, **kwargs: getattr(self._get_instance(), name)(
                *args, **kwargs
            )
        return value

_MISODE_VERSIONS_CACHE: list[dict] | None = None

def get_Minecraft_datapack_version(version: str, *, use_cache: bool = True) -> float:
    global _MISODE_VERSIONS_CACHE
    if _MISODE_VERSIONS_CACHE is None or not use_cache:

        with urllib.request.urlopen(
            "https://raw.githubusercontent.com/misode/mcmeta/summary/versions/data.json"
        ) as url:
            data = json.load(url)
            _MISODE_VERSIONS_CACHE = data

    for v in _MISODE_VERSIONS_CACHE:
        if v["id"] == version:
            if 'data_pack_version' in v:
                major = int(v["data_pack_version"])
                minor = 0
                if "data_pack_version_minor" in v:
                    minor = int(v["data_pack_version_minor"])
                return float(str(major) + "." + str(minor))
            else:
                raise ValueError(f"Version '{version}' does not have a data_pack_version.")
                
    raise ValueError(f"Version '{version}' not found in the misode/mcmeta data.")