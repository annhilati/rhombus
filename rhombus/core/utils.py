__all__ = [
    "JSONValue",
    "JSONDict",
    "BeetFile",
    "Annotation",
    "Decorator",
    "Dataclass",
    "DataclassInstance",
    "JSON_hash",
    "fields",
    "annotated_fields",
    "GlobalBinding",
    "get_Minecraft_datapack_version"
]

from typing import Callable, Any, get_type_hints
import typing
import types
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


_ADJECTIVES = [
    "agile", "brave", "calm", "clever", "cool", "crazy", "eager", "epic",
    "fierce", "fluffy", "flying", "frosty", "golden", "happy", "hidden",
    "jolly", "lazy", "lucky", "magic", "mighty", "mystic", "noble", "proud",
    "quiet", "rapid", "secret", "silent", "smart", "sneaky", "solid", "swift",
    "wild", "wise", "wooden", "yellow", "ancient", "angry", "awesome", "bold",
    "bouncy", "bright", "broken", "bumpy", "busy", "careful", "chilly", "chunky",
    "classic", "clean", "clumsy", "creepy", "crispy", "curious", "cute", "dark",
    "deadly", "deep", "dizzy", "dry", "dusty", "empty", "evil", "fancy", "fast",
    "fat", "fierce", "filthy", "fine", "flat", "fresh", "friendly", "funny",
    "gentle", "giant", "glad", "gloomy", "good", "great", "greedy", "green",
    "heavy", "holy", "hot", "huge", "hungry", "icy", "itchy", "kind", "large",
    "light", "little", "lonely", "long", "lost", "loud", "lovely", "mad", "mean"
]

_NOUNS = [
    "axolotl", "bee", "cat", "creeper", 
    "enderman", "fox", "frog", "ghast", "horse",
    "llama", "panda", "phantom",
    "piglin", "sheep", "slime", "spider", "squid",
    "turtle", "warden", "wolf", "zombie", "allay", "armadillo",
    "bat", "blaze", "breeze", "camel", "chicken", "cod", "cow", "dolphin",
    "donkey", "drowned", "evoker", "glowsquid", "goat",
    "hoglin", "husk", "illusioner", "magmacube", "mooshroom",
    "mule", "ocelot", "parrot", "pig", "pillager", "polarbear", "pufferfish",
    "rabbit", "ravager", "salmon", "shulker", "silverfish", "skeleton",
    "sniffer", "snowgolem", "stray", "strider", "tadpole", "vex",
    "villager", "vindicator", "witch", "wither", "zoglin"
]

def JSON_hash(data: JSONDict) -> str:
    """Creates a UUID-string without dashes based of a JSON dictionary.
    
    When `human_readable_names` is `True` in the active Rhombus environment,
    a more memorable word group is returned.
    """
    encoded_str = json.dumps(
        data, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("utf-8")
    hash_digest = hashlib.sha256(encoded_str).digest()
    
    from rhombus.runtime import rho
    if rho.human_readable_names:
        adj_idx = int.from_bytes(hash_digest[0:4], "little") % len(_ADJECTIVES)
        noun_idx = int.from_bytes(hash_digest[4:8], "little") % len(_NOUNS)
        num = int.from_bytes(hash_digest[8:12], "little") % 10000
        return f"{_ADJECTIVES[adj_idx]}_{_NOUNS[noun_idx]}_{num:04d}"
        
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
    try:
        hints = get_type_hints(o)
        return {f.name: hints[f.name] for f in flds if f.init and f.name in hints}
    except (NameError, TypeError):
        import typing, inspect
        hints = inspect.get_annotations(o if isinstance(o, type) else type(o), eval_str=False)
        return {f.name: hints.get(f.name, typing.Any) for f in flds if f.init}


def check_type(value: Any, annotation: Annotation) -> bool:
    
    if value is None:
        return True
    if annotation is typing.Any:
        return True
        
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    
    # Union types (e.g. A | B or Union[A, B])
    if origin is typing.Union or type(annotation) is getattr(types, "UnionType", type(None)):
        return any(check_type(value, arg) for arg in args)
        
    if origin is typing.Literal:
        return value in args
        
    if origin is list:
        if not isinstance(value, (list, tuple)):
            return False
        if not args:
            return True
        return all(check_type(v, args[0]) for v in value)
        
    if origin is dict:
        if not isinstance(value, dict):
            return False
        if not args:
            return True
        return all(check_type(k, args[0]) and check_type(v, args[1]) for k, v in value.items())

    if origin is tuple:
        if not isinstance(value, (list, tuple)):
            return False
        if not args:
            return True
        if len(args) == 2 and args[1] is ...:
            return all(check_type(v, args[0]) for v in value)
        if len(args) != len(value):
            return False
        return all(check_type(v, arg) for v, arg in zip(value, args))
        
    if isinstance(annotation, type):
        if annotation is float and isinstance(value, int):
            return True
        import enum
        if issubclass(annotation, enum.Enum):
            return isinstance(value, annotation) or value in [e.value for e in annotation]
            
        if type(value).__name__ == "UnresolvedVersionedNode":
            # UnresolvedVersionedNodes are placeholders for any RhombusASTNode subclass.
            # We skip strict validation since the actual type isn't known until resolution.
            return True
            
        return isinstance(value, annotation)
        
    return True


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


# ======// Minecraft Metadata //=================================================================//


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