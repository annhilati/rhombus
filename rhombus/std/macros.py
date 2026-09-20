"""The macro infrastructure of Rhombus."""

__all__ = ["macro", "implementation", "resolve_ast_versioning"]

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
from types import UnionType
import inspect
import functools
import sys

from rhombus.core.node import UnresolvedVersionedNode, resolve_ast_versioning
from rhombus.core.environment import DatapackVersion, VersionString, VersionTuple, _parse_version_specifier, get_module_addon_namespace, rho
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


_macro_registrations: list[tuple[Any, Any, Callable]] = []


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
        _macro_registrations.append((since, until, f))
        return f

    if func is not None:
        return decorator(func)
    return decorator


class MacroDispatcher:
    def __init__(self, func: Callable, repr_func: Callable | None = None):
        self.func = _create_argument_resolver(func)
        self.repr_func = repr_func


        self.default_ns = get_module_addon_namespace(func.__module__) or "datapack"

        functools.update_wrapper(self, func)
        self.__signature__ = inspect.signature(func)

        # Determine if we should evaluate lazily based on return annotation
        ret_anno = func.__annotations__.get("return")
        if ret_anno is None:
            self.returns_density = True
        else:
            ret_str = str(ret_anno)
            if "Density" in ret_str or "RhombusASTNode" in ret_str or "Any" in ret_str:
                self.returns_density = True
            else:
                self.returns_density = False

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        # Pre-validate arguments so we throw early if they are invalid
        self.__signature__.bind(*args, **kwargs)

        if self.returns_density:
            return Density(
                UnresolvedVersionedNode(
                    dispatcher=self,
                    args=args,
                    kwargs=kwargs,
                    repr_func=self.repr_func
                )
            )
        else:
            # If the macro explicitly returns something else (like an int or tuple),
            # we cannot use a lazy AST node placeholder. We must evaluate it immediately.
            return self._execute_for_version(*args, **kwargs)

    def _execute_for_version(self, *args: Any, **kwargs: Any) -> Any:
        global _macro_registrations
        _macro_registrations = []

        # Execute the wrapper to resolve AnyDensity to Density and call the inner function.
        # This will trigger the @implementation decorators and populate _macro_registrations.
        result = self.func(*args, **kwargs)

        impls = list(_macro_registrations)
        _macro_registrations = []

        if not impls:
            return result

        parsed_impls = []
        default_impl = None

        for since_v, until_v, impl_func in impls:
            p_since = _parse_version_specifier(since_v, default_namespace=self.default_ns) if since_v is not None else None
            p_until = _parse_version_specifier(until_v, default_namespace=self.default_ns) if until_v is not None else None
            
            if p_since is None and p_until is None:
                if default_impl is not None:
                    raise ValueError(
                        f"Multiple default implementations (without 'since' or 'until') found in macro '{self.__name__}'"
                    )
                default_impl = impl_func
            else:
                parsed_impls.append((p_since, p_until, impl_func))

        def _invoke(impl_f: Callable) -> Any:
            sig = inspect.signature(impl_f)
            if not sig.parameters:
                return impl_f()
            return _create_argument_resolver(impl_f)(*args, **kwargs)

        def _check(req_tuple: tuple[str, tuple[int, ...]]) -> bool:
            ns, req_v = req_tuple
            current_v = rho.versions.get(ns)
            if current_v is None:
                return False
            
            length = max(len(current_v), len(req_v))
            current_padded = tuple(list(current_v) + [0] * (length - len(current_v)))
            req_padded = tuple(list(req_v) + [0] * (length - len(req_v)))
            
            return current_padded >= req_padded

        valid_impls = []
        for p_since, p_until, impl_func in parsed_impls:
            if p_since is not None and not _check(p_since):
                continue
            if p_until is not None and _check(p_until):
                continue
            valid_impls.append(impl_func)
            
        if valid_impls:
            # If multiple valid implementations match, we use the last defined one
            return _invoke(valid_impls[-1])

        if default_impl is not None:
            return _invoke(default_impl)

        raise NotImplementedError(
            f"No valid implementation found for macro '{self.__name__}' at current environment versions."
        )


@overload
def macro[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...
@overload
def macro[**P, R](*, repr: Callable[["UnresolvedVersionedNode"], str] | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
def macro(
    func: Callable | None = None,
    *,
    repr: Callable[["UnresolvedVersionedNode"], str] | None = None
) -> Callable:
    """The **`macro`** decorator allows functions to use the `AnyDensity` type
    for annotation of its arguments to automatically resolve passed values to
    `Density` objects.

    It acts as an organizer for `@implementation` decorated inner functions.
    """
    def decorator(f: Callable) -> Callable:
        return cast(Callable, MacroDispatcher(f, repr_func=repr))
    
    if func is not None:
        return decorator(func)
    return decorator
