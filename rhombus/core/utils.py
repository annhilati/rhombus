from typing import Callable, Final, Any, get_type_hints
import hashlib, uuid, json, functools, inspect, dataclasses

import beet, beet.library.base


#======// Typing //==============================================================================//

type JSONValue = dict[str, JSONValue] | list[JSONValue] | tuple[JSONValue] | str | int | float | bool | None
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


#======// Data //================================================================================//

def uuid_hash(data: JSONDict) -> str:
    """Creates a UUID string without dashes based of a JSON dictionary."""
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
"Typing sentinel to denote that a value will be adopted from the environment."

def contextfunction[**P, R](**envparams: str) -> Decorator[P, R]:
    """Decorator for automatic context handling for parameters.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            
            # Import here to avoid circular imports if any
            from rhombus import config
            import copy

            needs_new_context = False
            overrides = {}

            for param, env_attr in envparams.items():
                value = bound.arguments.get(param)

                if value is FROM_CONTEXT:
                    bound.arguments[param] = getattr(config.env, env_attr)
                else:
                    needs_new_context = True
                    overrides[env_attr] = value

            if needs_new_context:
                # Get the actual environment object (the proxy exposes it via _current)
                # and create a shallow copy so we can override attributes safely
                current_env_obj = config.env._current
                new_env = copy.copy(current_env_obj)
                
                for attr, val in overrides.items():
                    setattr(new_env, attr, val)
                    
                token = config._current_env.set(new_env)
                try:
                    return func(*bound.args, **bound.kwargs)  # type: ignore
                finally:
                    config._current_env.reset(token)
            else:
                return func(*bound.args, **bound.kwargs)  # type: ignore

        wrapper.__signature__ = sig # type: ignore
        return wrapper
        
    return decorator


#======// Dataclasses //=========================================================================//

def fields(o: DataclassInstance) -> dict[str, Any]:
    "Returns the fields of a dataclass instance, that are present in the init, with their values."
    try:
        flds = dataclasses.fields(o)
    except TypeError:
        raise TypeError(f"must be called with a dataclass instance, not: {o}")
    return dict(sorted({
        f.name: getattr(o, f.name, None)
        for f in flds
        if f.init
    }.items()))

def annotated_fields(o: Dataclass) -> dict[str, Annotation]:
    "Returns the fields of a dataclass, that are present in the init, with their annotation."
    try:
        flds = dataclasses.fields(o)
    except TypeError:
        raise TypeError(f"must be called with a dataclass type or instance, not: {o}")
    return {
        f.name: get_type_hints(o)[f.name]
        for f in flds
        if f.init
    }