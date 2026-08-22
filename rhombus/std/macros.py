"""The macro infrastructure of Rhombus."""

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
    overload,
)
from types import NotImplementedType, UnionType
import inspect
import functools
import logging
import sys

from rhombus.core.environment import DatapackVersion
from rhombus.core.utils import Annotation
from rhombus.std.density import Density, AnyDensity


def _create_argument_resolver(func: Callable) -> Callable:
    """Wraps a function to automatically resolve AnyDensity arguments to Density objects."""
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

        if origin is Union or isinstance(hint, UnionType):
            return any(is_anydensity_hint(arg) for arg in get_args(hint))

        return False

    def resolve_value(val: Any, hint: Annotation) -> Any:
        origin = get_origin(hint)
        args = get_args(hint)

        # Leaf: AnyDensity -> Density(...)
        if is_anydensity_hint(hint):
            return val if isinstance(val, Density) else Density(val)

        # Union / |: try the first matching branch
        if origin is Union or isinstance(hint, UnionType):
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
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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
    return wrapper


class MacroDispatcher:
    def __init__(self, default_func: Callable):
        self.default_impl = _create_argument_resolver(default_func)
        self.registry: list[tuple[DatapackVersion, Callable | NotImplementedType]] = []
        
        # Override the __name__ and __doc__ back to the original for clarity
        functools.update_wrapper(self, default_func)
        self.__signature__ = inspect.signature(default_func)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        from rhombus.core.environment import env
        logger = logging.getLogger(__name__)
        
        if env.datapack_version is None:
            # If no target version is set, default to the main implementation.
            return self.default_impl(*args, **kwargs)
            
        try:
            target_v = float(env.datapack_version)
        except Exception:
            logger.warning(
                f"Invalid target version in environment: {env.datapack_version}. "
                f"Using default implementation for {self.__name__}."
            )
            return self.default_impl(*args, **kwargs)
            
        # self.registry is expected to be sorted by 'until' ascending
        for until_v, impl in self.registry:
            if target_v < until_v:
                if impl is NotImplemented:
                    from rhombus.core.environment import RhombusVersionError
                    raise RhombusVersionError(
                        f"Macro '{self.__name__}' is not supported in datapack version {target_v} "
                        f"(requires >= {until_v})"
                    )
                return impl(*args, **kwargs)
                
        # If no registered version matched (target_v >= all untils), fall back to the default implementation.
        return self.default_impl(*args, **kwargs)

@overload
def macro[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...

@overload
def macro[**P, R](*versions: tuple[DatapackVersion, Callable | NotImplementedType]) -> Callable[[Callable[P, R]], Callable[P, R]]: ...

def macro(*args: Any) -> Any:
    """The **`macro`** decorator allows functions to use the `AnyDensity` type
    for annotation of its arguments to automatically resolve passed values to
    `Density` objects.
    
    It also acts as a version dispatcher. Legacy implementations can be 
    provided as positional tuples: `(until_version, implementation_func)`.
    If an implementation is impossible for a given version, pass `NotImplemented`.
    """
    if len(args) == 1 and callable(args[0]) and not isinstance(args[0], tuple):
        return cast(Callable, MacroDispatcher(args[0]))
    
    def decorator(func: Callable) -> Callable:
        dispatcher = MacroDispatcher(func)
        
        # Validate and sort versions by 'until' ascending
        seen = set()
        sorted_versions = sorted(args, key=lambda x: x[0])
        
        for until_v, impl in sorted_versions:
            if until_v in seen:
                raise ValueError(f"Duplicate 'until' version {until_v} in macro '{func.__name__}'")
            seen.add(until_v)
            
            if impl is NotImplemented:
                dispatcher.registry.append((until_v, NotImplemented))
            else:
                dispatcher.registry.append((until_v, _create_argument_resolver(impl)))
                
        return cast(Callable, dispatcher)
    return decorator
