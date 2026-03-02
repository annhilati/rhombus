from typing import Callable, Final, Any, get_type_hints
import hashlib, uuid, json, functools, inspect, dataclasses, contextvars

__all__ = ["uuid_hash", "JSONDict", "contextfunction", "FROM_CONTEXT"]


#======// Typing //==============================================================================//

type JSONDict = dict[str, dict | list | tuple | str | int | float | bool]
type DataclassInstance = object
type Dataclass = type
type Decorator[**P, T] = Callable[[Callable[P, T]], Callable[P, T]]


#======// Data //================================================================================//

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


#======// Context //=============================================================================//

FROM_CONTEXT: Final = object()
"Typing sentinel to denote that a value will be taken from a context variable."

def contextfunction(**ctxparams: contextvars.ContextVar) -> Decorator:
    """Decorator for automatic context handling for parameters.
    
    All kwargs in this decorator, that are also present as kwargs in the decorated function are affected.

    If `FROM_CONTEXT` is passed:
        Calls the function with the current value of the `ContextVar` of the corresponding decorator kwarg
    If something else is passed:
        Sets the `ContextVar` of the corresponding decorator kwarg and then calls the function

    This decorator can also be used without `FROM_CONTEXT` entirely, as a tool to set `ContextVar`s.
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()

            tokens: dict[contextvars.ContextVar, list[contextvars.Token]] = {}

            for param, ctxvar in ctxparams.items():
                value = bound.arguments.get(param)

                if value is FROM_CONTEXT:
                    current = ctxvar.get(None)
                    bound.arguments[param] = current
                else:
                    tokens.setdefault(ctxvar, []).append(ctxvar.set(value))

            try:
                return func(*bound.args, **bound.kwargs)
            finally:
                for ctxvar, token_list in tokens.items():
                    for token in reversed(token_list):
                        ctxvar.reset(token)

        return wrapper
    return decorator


#======// Dataclasses //=========================================================================//

def fields(o: DataclassInstance) -> dict[str, Any]:
    "Returns the fields of a dataclass instance, that are present in the init, with their values."
    return {
        f.name: getattr(o, f.name, None)
        for f in dataclasses.fields(o)
        if f.init
    }

def annotated_fields(o: Dataclass) -> dict[str, type]:
    "Returns the fields of a dataclass, that are present in the init, with their annotation."
    return {
        f.name: get_type_hints(o)[f.name]
        for f in dataclasses.fields(o)
        if f.init
    }