from typing import Union, TypeAliasType, Literal, Any, get_origin, get_args
from types import UnionType

from rhombus.core.utils import JSONValue
from rhombus.core.node import RhombusASTNode

__all__ = ["serialize_any_toplevel", "serialize_any_inline", "deserialize_any_toplevel", "deserialize_any_inline"]  


def serialize_any_toplevel[T](o: T) -> JSONValue:
    """Main serialization function for top-level values."""

    if isinstance(o, RhombusASTNode):
        return o.serialize_toplevel()
    
    # Correct me if I'm wrong but there aren't any other valid cases?
    raise NotImplementedError(
        "serialize_any_toplevel() was called with a value of a type that is not 'RhombusASTNode' "
        "This is unexpected and unknown how to handle."
    )

def serialize_any_inline[T](o: T) -> JSONValue:
    """Main serialization function for nested/inline values."""
    
    if isinstance(o, RhombusASTNode):
        return o.serialize_inline()
    
    elif isinstance(o, (list, set, tuple)):
        return list(serialize_any_inline(m) for m in o)
    
    elif isinstance(o, dict):
        return {serialize_any_inline(k): serialize_any_inline(v) for k, v in o.items()}
    
    return o # Other JSONValues should be fine literally
    
    
def deserialize_any_toplevel[T](v: Any, t: type[T]) -> T:
    """Main deserialization function for top-level values."""
    return _deserialize_any(v, t, top_level=True)


def deserialize_any_inline[T](v: Any, t: type[T]) -> T:
    """Main deserialization function for nested/inline values."""
    return _deserialize_any(v, t, top_level=False)


def _deserialize_any[T](v: Any, t: type[T], *, top_level: bool) -> T:
    origin = get_origin(t)

    if origin is None:
        if isinstance(t, TypeAliasType):
            return _deserialize_any(v, t.__value__, top_level=top_level)

        if isinstance(t, type):
            if issubclass(t, RhombusASTNode):
                if top_level:
                    return t.deserialize_toplevel(v)
                return t.deserialize_inline(v)

            if t is str:
                return str(v)  # type: ignore[return-value]
            if t is int:
                return int(v)  # type: ignore[return-value]
            if t is float:
                return float(v)  # type: ignore[return-value]
            if t is bool:
                return bool(v)  # type: ignore[return-value]
            if t is type(None):
                if v is None:
                    return None  # type: ignore[return-value]
                raise ValueError(f"Expected None, got {v!r}")

        if t is Any:
            return v

        raise ValueError(f"No deserialization procedure for target type '{t}' known")

    args = get_args(t)

    if origin is Literal:
        if v in args:
            return v  # type: ignore[return-value]
        raise ValueError(f"Value {v!r} is not one of the allowed Literal values {args!r}")

    if origin in (list, set):
        inner_t = args[0] if len(args) == 1 else Union[*args]
        items = [_deserialize_any(m, inner_t, top_level=False) for m in v]
        return origin(items)  # type: ignore[return-value]

    if origin is tuple:
        if len(args) == 2 and args[1] is Ellipsis:
            inner_t = args[0]
            return tuple(_deserialize_any(m, inner_t, top_level=False) for m in v)  # type: ignore[return-value]
        return tuple(
            _deserialize_any(m, arg, top_level=False)
            for m, arg in zip(v, args)
        )  # type: ignore[return-value]

    if origin in (Union, UnionType):

        for arg in args:
            if arg is type(None) and v is None:
                return None  # type: ignore[return-value]
            if isinstance(arg, type) and isinstance(v, arg):
                try:
                    return _deserialize_any(v, arg, top_level=top_level)
                except Exception:
                    pass

        for arg in args:
            try:
                return _deserialize_any(v, arg, top_level=top_level)
            except Exception:
                continue

        raise ValueError(f"Cannot deserialize {v!r} into {t!r}")

    if origin is dict:
        kt, vt = args
        return {
            _deserialize_any(k, kt, top_level=False): _deserialize_any(val, vt, top_level=False)
            for k, val in v.items()
        }  # type: ignore[return-value]

    raise ValueError(f"No deserialization procedure for target type '{t}' known")