from typing import Callable, Final, Any, ClassVar, get_type_hints, get_origin
import hashlib, uuid, json, functools, inspect, dataclasses, contextvars, dataclasses, collections

import beet, beet.library.base


#======// Typing //==============================================================================//

type JSONValue = dict[str, JSONValue] | list[JSONValue] | tuple[JSONValue] | str | int | float | bool | None
type JSONDict = dict[str, JSONValue]
class BeetFile(beet.library.base.NamespaceFile):
    data: JSONDict
    encoder: Callable[[JSONDict], str]
    decoder: Callable[[str], JSONDict]

type Annotation = type
type Dataclass = type
type DataclassInstance = object
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

def contextfunction[**P, R](**ctxparams: contextvars.ContextVar) -> Decorator[P, R]:
    """Decorator for automatic context handling for parameters.
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
    try:
        flds = dataclasses.fields(o)
    except TypeError:
        raise TypeError(f"must be called with a dataclass type or instance, not: {o}")
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


_MISSING = object()

@dataclasses.dataclass
class Field:
    default: Any = _MISSING
    init: bool = True
    annotation: Annotation = dataclasses.field(default=_MISSING, init=False)

def _collect_fields(cls) -> dict[str, Field]:
    """
    Sammelt Felder in MRO-Reihenfolge:
    ältere Basisklassen zuerst, dann jüngere, dann die Klasse selbst.
    ClassVar wird ignoriert.

    Rückgabe:
        dict[str, Field]
    """
    ordered: dict[str, Field] = collections.OrderedDict()

    def add_from(owner) -> None:
        ann = getattr(owner, "__annotations__", {})
        for name, annotation in ann.items():
            if _is_classvar(annotation):
                continue

            value = owner.__dict__.get(name, _MISSING)

            if isinstance(value, Field):
                fld = value
            else:
                fld = Field(default=value)

            fld.annotation = annotation
            ordered[name] = fld

    # Basisklassen zuerst, dann die Klasse selbst
    for base in cls.__mro__[-2:0:-1]:  # ohne object und ohne cls
        add_from(base)

    add_from(cls)

    return dict(ordered)

def _is_classvar(annotation: Any) -> bool:
    if annotation is ClassVar:
        return True
    if isinstance(annotation, str):
        s = annotation.replace("typing.", "")
        return s == "ClassVar" or s.startswith("ClassVar[")
    return get_origin(annotation) is ClassVar

def _default_for(owner: type[Any], name: str):
    """
    Default aus der Klassenhierarchie holen, wenn vorhanden.
    """
    if name in owner.__dict__:
        return owner.__dict__[name]

    for base in owner.__mro__[1:]:
        if name in base.__dict__:
            return base.__dict__[name]

    return _MISSING

def _make_init(cls, fields: dict[str, Field]):
    """
    Baut eine echte __init__-Funktion mit passender Signatur.
    """
    params = [inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD)]
    for name, field in fields.items():
        if field.default is _MISSING:
            params.append(inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD))
        else:
            params.append(inspect.Parameter(
                name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=field.default,
            ))

    signature = inspect.Signature(params)

    field_names = [name for name in fields]
    defaults = {name: f.default for name, f in fields.items()}

    def __init__(self, *args, **kwargs):
        if len(args) > len(field_names):
            raise TypeError(
                f"{cls.__name__}.__init__() takes at most {len(field_names) + 1} "
                f"positional arguments but {len(args) + 1} were given"
            )

        values = {}
        consumed_kwargs = set()

        for i, name in enumerate(field_names):
            if i < len(args):
                if name in kwargs:
                    raise TypeError(
                        f"{cls.__name__}.__init__() got multiple values for argument {name!r}"
                    )
                values[name] = args[i]
                continue

            if name in kwargs:
                values[name] = kwargs[name]
                consumed_kwargs.add(name)
                continue

            if defaults[name] is _MISSING:
                raise TypeError(
                    f"{cls.__name__}.__init__() missing required argument: {name!r}"
                )
            values[name] = defaults[name]

        unexpected = [k for k in kwargs.keys() if k not in consumed_kwargs]
        if unexpected:
            raise TypeError(
                f"{cls.__name__}.__init__() got unexpected keyword arguments: "
                + ", ".join(repr(x) for x in unexpected)
            )

        for name, value in values.items():
            setattr(self, name, value)

    __init__.__signature__ = signature  # für inspect.signature(...)
    __init__.__qualname__ = f"{cls.__qualname__}.__init__"
    return __init__