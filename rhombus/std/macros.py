"""The macro infrastructure of Rhombus."""

__all__ = ["macro", "implementation"]

from typing import (
    Callable,
    Any,
    Annotated,
    Union,
    get_type_hints,
    get_args,
    get_origin,
    overload,
)
from types import UnionType
import inspect
import functools
import sys

from rhombus.core.ast import RhombusASTNode, lazy as core_macro, implementation as core_implementation
from rhombus.core.environment import DatapackVersion, VersionString, VersionTuple
from rhombus.core.utils import Annotation, Decorator
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
        if is_anydensity_hint(hint) or hint is __import__("rhombus.std.density", fromlist=["Density"]).Density or str(hint) == "Density" or str(hint) == "~Density":
            return val if isinstance(val, __import__("rhombus.std.density", fromlist=["Density"]).Density) else __import__("rhombus.std.density", fromlist=["Density"]).Density(val)

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
                    bound.arguments[name] = tuple(resolve_value(v, hint) for v in value)
                elif param.kind == inspect.Parameter.VAR_KEYWORD:
                    bound.arguments[name] = {
                        k: resolve_value(v, hint) for k, v in value.items()
                    }
                else:
                    bound.arguments[name] = resolve_value(value, hint)

        return func(*bound.args, **bound.kwargs)

    wrapper.__signature__ = sig
    return wrapper

def _coerce_node(res: Any) -> Any:
    if not isinstance(res, Density):
        try:
            res = Density(res)
        except Exception as e:
            raise TypeError(f"Macro returned {type(res)}, which could not be converted to a Density object.") from e
    if hasattr(res, "AST"):
        return res.AST
    return res

def implementation(
    func: Callable | None = None, 
    *, 
    since: DatapackVersion | VersionString | VersionTuple | None = None,
    until: DatapackVersion | VersionString | VersionTuple | None = None
):
    """Decorator for inner functions inside a macro to register them as implementations.
    If 'until' is None, it acts as the default fallback implementation.
    """
    def decorator(f: Callable):
        f_resolved = _create_argument_resolver(f)
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return _coerce_node(f_resolved(*args, **kwargs))
            
        wrapper.__signature__ = inspect.signature(f_resolved)
        return core_implementation(since=since, until=until)(wrapper)

    if func is not None:
        return decorator(func)
    return decorator


@overload
def macro[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...
@overload
def macro[**P, R](*, repr: Callable[["RhombusASTNode"], str] | None = None) -> Decorator[P, R]: ...
def macro(
    func: Callable | None = None,
    *,
    repr: Callable[["RhombusASTNode"], str] | None = None
) -> Callable:
    """The **`macro`** decorator allows functions to use special behaviour beneficial for writing density functions:
    
    - Values for parameters annotated with `AnyDensity` will automatically be coerced to the `Density` type.
    - Allows defining functions decorated with the `@implementation` decorator inside the function to provide lazily chosen version-dependent implementations.
    - Allows using Python's `if / elif / else` syntax as well as special macros with `with`-statements inside the function.
    """
    def decorator(f: Callable) -> Callable:
        from rhombus.std.conditional.ast_parser import transform_ast # avoid circular import
        f_transformed = transform_ast(f)
        f_resolved = _create_argument_resolver(f_transformed)
        
        @functools.wraps(f)
        def base_wrapper(*args, **kwargs):
            res = f_resolved(*args, **kwargs)
            from rhombus.core.ast import _macro_registrations
            if _macro_registrations:
                return res
            return _coerce_node(res)
        base_wrapper.__signature__ = inspect.signature(f_resolved)

        core_dispatcher = core_macro(repr=repr)(base_wrapper)
        
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ast_node = core_dispatcher(*args, **kwargs)
            return Density(ast_node)
            
        wrapper.__signature__ = inspect.signature(f_resolved)
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator



