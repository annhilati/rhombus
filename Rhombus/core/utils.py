from typing import TypeAlias, Callable, TypeVar, ParamSpec, Final
import hashlib, uuid, json, functools, inspect

__all__ = ["uuid_hash", "JSONDict", "with_datapack_context", "FROM_CONTEXT"]

JSONDict: TypeAlias = dict[str, dict | list | tuple | str | int | float | bool | None]

def uuid_hash(data: JSONDict) -> str:
    """Creates a UUID string (without `-`) based of a JSON dictionary."""
    encoded_str = json.dumps(
        data, 
        sort_keys=True, 
        ensure_ascii=True, 
        separators=(',', ':')
    ).encode('utf-8')
    hash_digest = hashlib.sha256(encoded_str).digest()
    return str(uuid.UUID(bytes=hash_digest[:16])).replace("-", "")

_P = ParamSpec("P")
_R = TypeVar("R")

FROM_CONTEXT: Final = object()
"Typing sentinel to denote that a value will be taken from a context variable."

def with_datapack_context(func: Callable[_P, _R], kwarg: str = "dp") -> Callable[_P, _R]:
    """Decorator to help with DataPack context when decoding.
    
    If the kwarg stated in `arg` of the decorated function is `FROM_CONTEXT`:
        Calls the decorated function with the current datapack context (which can be `None`, so this should be checked).
    If the kwarg stated in `arg` of the decorated function is set:
        Sets the datapack context for the execution of the decorated function.
    """
    from Rhombus import config
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        dp = bound.arguments.get(kwarg)

        if dp is FROM_CONTEXT:
            current = config.datapack_context.get(None)
            bound.arguments[kwarg] = current
            return func(*bound.args, **bound.kwargs)

        token = config.datapack_context.set(dp)
        try:
            return func(*bound.args, **bound.kwargs)
        finally:
            config.datapack_context.reset(token)

    return wrapper