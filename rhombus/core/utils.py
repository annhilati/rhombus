from typing import Callable, Final, Any, get_type_hints, ClassVar
import hashlib, uuid, json, functools, inspect, dataclasses, contextvars, beet, beet.library.base


#======// Typing //==============================================================================//

type JSONValue = dict[str, JSONValue] | list[JSONValue] | tuple[JSONValue] | str | int | float | bool | None
type JSONDict = dict[str, JSONValue]
type Annotation = type
type DataclassInstance = object
type Dataclass = type
type Decorator[**P, T] = Callable[[Callable[P, T]], Callable[P, T]]
class BeetFile(beet.library.base.NamespaceFile):
    data: JSONDict | JSONValue | Any
    scope: ClassVar[beet.library.base.NamespaceFileScope]
    extension: ClassVar[str]

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

def contextfunction[**P, R](**ctxparams: contextvars.ContextVar) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for automatic context handling for parameters.
    ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
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
                # Type-Checker wissen manchmal nicht, dass bind_partial die exakten Args wiederherstellt, 
                # ein # type: ignore kann bei strenger Typisierung hier für mypy nötig sein,
                # aber die Signatur nach außen bleibt erhalten.
                return func(*bound.args, **bound.kwargs)  # type: ignore
            finally:
                for ctxvar, token_list in tokens.items():
                    for token in reversed(token_list):
                        ctxvar.reset(token)

        # Für die Laufzeit-Introspektion (z.B. pydantic oder FastAPI)
        wrapper.__signature__ = sig # type: ignore
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

def annotated_fields(o: Dataclass) -> dict[str, Annotation]:
    "Returns the fields of a dataclass, that are present in the init, with their annotation."
    return {
        f.name: get_type_hints(o)[f.name]
        for f in dataclasses.fields(o)
        if f.init
    }