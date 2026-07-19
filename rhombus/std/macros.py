__all__ = ["macro"]

from typing import (
    Callable,
    Any,
    Annotated,
    Union,
    cast,
    get_type_hints,
    get_args,
    get_origin,
)
import inspect
import functools
import sys
import types

from rhombus.core.utils import Annotation
from rhombus.std.density import Density, AnyDensity


def macro[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    """The **`macro`** decorator allows functions to use the `AnyDensity` type
    for annotation of its arguments to automatically resolve passed values to
    `Density` objects. This is usefull to allow shorthands such as literal
    numbers or reference strings without encountering type errors or having
    to deal with type unification.
    """

    def decorator[**P, R](func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)
        module = sys.modules[func.__module__]

        hints = get_type_hints(
            func,
            globalns=module.__dict__,
            include_extras=True,
        )

        def is_anydensity_hint(hint: Annotation) -> bool:
            if hint is AnyDensity:
                return True

            origin = get_origin(hint)

            if origin is Annotated:
                return is_anydensity_hint(get_args(hint)[0])

            if origin is Union or isinstance(hint, types.UnionType):
                return any(is_anydensity_hint(arg) for arg in get_args(hint))

            return False

        def resolve_value(val: Any, hint: Annotation) -> Any:
            origin = get_origin(hint)
            args = get_args(hint)

            # Leaf: AnyDensity -> Density(...)
            if is_anydensity_hint(hint):
                return val if isinstance(val, Density) else Density(val)

            # Union / |: try the first matching branch
            if origin is Union or isinstance(hint, types.UnionType):
                first_exception: Exception | None = None

                for arg in args:
                    try:
                        return resolve_value(val, arg)
                    except Exception as exc:
                        if first_exception is None:
                            first_exception = exc

                if first_exception is not None:
                    raise first_exception
                return val

            # Containers: recurse
            try:
                if origin is list and args:
                    return [resolve_value(v, args[0]) for v in val]

                if origin is set and args:
                    return {resolve_value(v, args[0]) for v in val}

                if origin is tuple and args:
                    # tuple[T, ...]
                    if len(args) == 2 and args[1] is Ellipsis:
                        return tuple(resolve_value(v, args[0]) for v in val)
                    # tuple[T1, T2, ...]
                    return tuple(resolve_value(v, a) for v, a in zip(val, args))

                if origin is dict and args:
                    k_hint, v_hint = args
                    return {
                        resolve_value(k, k_hint): resolve_value(v, v_hint)
                        for k, v in val.items()
                    }

            except TypeError:
                return val

            return val

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            for name, value in bound.arguments.items():
                hint = hints.get(name)
                if hint is not None:
                    param = sig.parameters[name]
                    if param.kind == inspect.Parameter.VAR_POSITIONAL:
                        bound.arguments[name] = tuple(
                            resolve_value(v, hint) for v in value
                        )
                    elif param.kind == inspect.Parameter.VAR_KEYWORD:
                        bound.arguments[name] = {
                            k: resolve_value(v, hint) for k, v in value.items()
                        }
                    else:
                        bound.arguments[name] = resolve_value(value, hint)

            return func(*bound.args, **bound.kwargs)

        wrapper.__signature__ = sig
        return cast(Callable[P, R], wrapper)

    return cast(Callable[P, R], decorator(fn))
