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

from rhombus.core.abstract import RhombusASTNode, LazyDispatcher, register_implementation, has_implementation_registrations
from rhombus.core.environment import DatapackVersion, VersionString, VersionTuple
from rhombus.core.utils import Annotation, Decorator
from rhombus.std.density import Density, AnyDensity

def _create_argument_processor[**P, R](
    func: Callable[P, R],
) -> tuple[
    Callable[..., tuple[tuple[Any, ...], dict[str, Any]]],
    Callable[P, R],
    inspect.Signature,
]:
    """Sets up argument resolution for AnyDensity arguments to Density objects."""
    sig = inspect.signature(func)
    module = sys.modules.get(func.__module__)
    globalns = module.__dict__ if module is not None else None

    try:
        hints = get_type_hints(
            func,
            globalns=globalns,
            include_extras=True,
        )
    except Exception:
        hints = getattr(func, "__annotations__", {})

    def hints_AnyDensity(hint: Annotation) -> bool:
        if hint is AnyDensity:
            return True

        origin = get_origin(hint)

        if origin is Annotated:
            return hints_AnyDensity(get_args(hint)[0])

        if origin is Union or isinstance(hint, UnionType):
            return any(hints_AnyDensity(arg) for arg in get_args(hint))

        return False

    def resolve_value(val: Any, hint: Annotation) -> Any:
        # Leaf: AnyDensity -> Density(...)
        if hints_AnyDensity(hint) or hint is Density or str(hint) == "Density" or str(hint) == "~Density":
            if isinstance(val, Density):
                return val
            return Density(val)

        origin = get_origin(hint)
        args = get_args(hint)

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

    def _resolve_bound(bound: inspect.BoundArguments) -> None:
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

    def process_args(*args: Any, **kwargs: Any) -> tuple[tuple[Any, ...], dict[str, Any]]:
        bound = sig.bind(*args, **kwargs)
        _resolve_bound(bound)
        return bound.args, bound.kwargs

    @functools.wraps(func)
    def resolved_func(*args: Any, **kwargs: Any) -> Any:
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        _resolve_bound(bound)
        return func(*bound.args, **bound.kwargs)

    resolved_func.__signature__ = sig
    return process_args, resolved_func, sig


def _create_argument_resolver[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Wraps a function to automatically resolve AnyDensity arguments to Density objects."""
    return _create_argument_processor(func)[1]


def _coerce_node(res: Density | AnyDensity):
    if not isinstance(res, Density):
        try:
            res = Density(res)
        except Exception as e:
            raise TypeError(f"Macro returned {type(res)}, which could not be converted to a Density object.") from e
    return res.AST


@overload
def macro[**P](
    func: Callable[P, Any],
    *,
    repr: Callable[["RhombusASTNode"], str] | None = None,
) -> Callable[P, Density]: ...
@overload
def macro[**P](
    *,
    repr: Callable[["RhombusASTNode"], str] | None = None,
) -> Callable[[Callable[P, Any]], Callable[P, Density]]: ...
def macro(
    func: Callable | None = None,
    *,
    repr: Callable[["RhombusASTNode"], str] | None = None
) -> Callable:
    """The **`macro`** decorator allows functions to use special behaviour beneficial for writing density functions:
    
    - Values for parameters annotated with `AnyDensity` will automatically be coerced to the `Density` type.
    - Allows defining functions decorated with the `@implementation` decorator inside the function to provide lazily chosen version-dependent implementations.
    - Allows using Python's `if / elif / else` syntax as well as special macros with `with`-statements inside the function.
    
    **NOTE:** All macros are pricipially lazy and will not be executed until the build process is issued.
    Thus `~.build()` can be called on `Density` type arguments without any problems to allow finer manipulation of the density function nodes.
    
    ## Usage:
    ```
    @macro
    def floor(df: AnyDensity, decimals: int = 0) -> Density:
        do_something() # everything before implementation declarations will be executed too
        
        @implementation(until=111)
        def floor():
            return ...
        
        @implementation
        def floor():
            return ...
    ```
    """
    def decorator(f: Callable) -> Callable:
        from rhombus.std.conditional.ast_parser import transform_ast # avoid circular import
        f_transformed = transform_ast(f)
        process_args, f_resolved, sig = _create_argument_processor(f_transformed)
        
        @functools.wraps(f)
        def base_wrapper(*args, **kwargs):
            res = f_resolved(*args, **kwargs)
            if has_implementation_registrations():
                return res
            return _coerce_node(res)
        base_wrapper.__signature__ = sig

        core_dispatcher = LazyDispatcher(base_wrapper, repr_func=repr)
        
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            resolved_args, resolved_kwargs = process_args(*args, **kwargs)
            ast_node = core_dispatcher(*resolved_args, **resolved_kwargs)
            return Density(ast_node)
            
        wrapper.__signature__ = sig
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator

@overload
def implementation[**P, R](
    func: Callable[P, R],
    *,
    since: DatapackVersion | VersionString | VersionTuple = None,
    until: DatapackVersion | VersionString | VersionTuple = None,
) -> Callable[P, R]: ...
@overload
def implementation[**P, R](
    *,
    since: DatapackVersion | VersionString | VersionTuple = None,
    until: DatapackVersion | VersionString | VersionTuple = None,
) -> Decorator[P, R]: ...
def implementation(
    func: Callable | None = None, 
    *, 
    since: DatapackVersion | VersionString | VersionTuple = None,
    until: DatapackVersion | VersionString | VersionTuple = None
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
        register_implementation(wrapper, since=since, until=until)
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator
