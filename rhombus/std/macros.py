"""The macro infrastructure of Rhombus."""

__all__ = ["macro", "implementation"]

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
import dataclasses
import inspect
import functools
import sys

from rhombus.core.node import RhombusASTNode, transform
from rhombus.core.density_function import DensityFunction
from rhombus.core.environment import DatapackVersion, VersionString, VersionTuple, _parse_version_specifier, get_module_addon_namespace
from rhombus.core.utils import Annotation, Decorator
from rhombus.std.density import Density, AnyDensity
from rhombus.runtime import rho

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
        from rhombus.std.conditional.ast_parser import transform_ast # avoid circular import
        func = transform_ast(func)
        self.func = _create_argument_resolver(func)
        self.repr_func = repr_func

        self.default_ns = get_module_addon_namespace(func.__module__) or "datapack"

        functools.update_wrapper(self, func)
        self.__signature__ = inspect.signature(func)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        # Pre-validate arguments so we throw early if they are invalid
        self.__signature__.bind(*args, **kwargs)

        return Density(
            UnresolvedMacroDensityFunction(
                dispatcher=self,
                args=args,
                kwargs=kwargs,
                repr_func=self.repr_func
            )
        )

    def _execute_for_version(self, *args: Any, **kwargs: Any) -> Any:
        global _macro_registrations
        _macro_registrations = []

        # Execute the wrapper to resolve AnyDensity to Density and call the inner function.
        # This will trigger the @implementation decorators and populate _macro_registrations.
        result = self.func(*args, **kwargs)

        impls = list(_macro_registrations)
        _macro_registrations = []

        def _coerce_density(res: Any) -> "Density":
            if not isinstance(res, Density):
                try:
                    res = Density(res)
                except Exception as e:
                    raise TypeError(f"Macro '{self.__name__}' returned {type(res)}, which could not be converted to a Density object.") from e
            return res

        if not impls:
            return _coerce_density(result)

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
                return _coerce_density(impl_f())
            return _coerce_density(_create_argument_resolver(impl_f)(*args, **kwargs))

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
            f"No implementation found for macro '{self.__name__}' for versions: {rho.versions}."
        )



@overload
def macro[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...
@overload
def macro[**P, R](*, repr: Callable[["UnresolvedMacroDensityFunction"], str] | None = None) -> Decorator[P, R]: ...
def macro(
    func: Callable | None = None,
    *,
    repr: Callable[["UnresolvedMacroDensityFunction"], str] | None = None
) -> Callable:
    """The **`macro`** decorator allows functions to use special behaviour beneficial for writing density functions:
    
    - Values for parameters annotated with `AnyDensity` will automatically be coerced to the `Density` type.
    - Allows defining functions decorated with the `@implementation` decorator inside the function to provide lazily chosen version-dependent implementations.
    - Allows using Python's `if / elif / else` syntax as well as special macros with `with`-statements inside the function.
    """
    def decorator(f: Callable) -> Callable:
        return cast(Callable, MacroDispatcher(f, repr_func=repr))
    
    if func is not None:
        return decorator(func)
    return decorator


class UnresolvedMacroDensityFunction(DensityFunction):
    dispatcher: Callable = dataclasses.field(repr=False, compare=False)
    args: tuple[Any, ...] = dataclasses.field(repr=False, compare=False)
    kwargs: dict[str, Any] = dataclasses.field(repr=False, compare=False)
    repr_func: Callable[["UnresolvedMacroDensityFunction"], str] | None = dataclasses.field(
        default=None, repr=False, compare=False
    )

    _cached_version: Any = dataclasses.field(init=False, default=None, repr=False, compare=False)
    _cached_node: RhombusASTNode | None = dataclasses.field(
        init=False, default=None, repr=False, compare=False
    )

    def __repr__(self) -> str:
        if self.repr_func is not None:
            return self.repr_func(self)
        parts = [repr(arg) for arg in self.args]
        parts.extend(f"{k}={repr(v)}" for k, v in self.kwargs.items())
        return f"{self.dispatcher.__name__}({', '.join(parts)})"

    def resolve(self) -> RhombusASTNode:
        current_version = rho.datapack_version

        if self._cached_version == current_version and self._cached_node is not None:
            return self._cached_node

        result = self.dispatcher._execute_for_version(*self.args, **self.kwargs) # type: ignore
        object.__setattr__(self, "_cached_version", current_version)

        if hasattr(result, "AST") and isinstance(result.AST, RhombusASTNode):
            object.__setattr__(self, "_cached_node", result.AST)
        elif isinstance(result, RhombusASTNode):
            object.__setattr__(self, "_cached_node", result)
        else:
            raise TypeError(
                f"Version node dispatcher returned invalid type: {type(result)}"
            )

        return self._cached_node

    def serialize_inline(self):
        return self.resolve().serialize_inline()

    def serialize_toplevel(self):
        return self.resolve().serialize_toplevel()

    @property
    def inscribed_toplevel_nodes(self) -> set[RhombusASTNode]:
        return self.resolve().inscribed_toplevel_nodes

def resolve_macro_densityfunction(node: RhombusASTNode) -> RhombusASTNode:
    def _resolver(n: RhombusASTNode) -> RhombusASTNode:
        if isinstance(n, UnresolvedMacroDensityFunction):
            return resolve_macro_densityfunction(n.resolve())
        return n
    return transform(node, _resolver)
