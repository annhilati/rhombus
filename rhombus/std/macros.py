"""The macro infrastructure of Rhombus."""

__all__ = ["macro", "implementation", "resolve_ast"]

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
import copy

from rhombus.core.node import RhombusASTNode
from rhombus.core.environment import RhombusVersion, VersionLike, get_module_version_namespace, env
from rhombus.core.utils import Annotation
from rhombus.core.density_function import DensityFunction
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


_macro_registrations: list[tuple[Any, Callable]] = []


def implementation(func: Callable | None = None, *, until: VersionLike | None = None):
    """Decorator for inner functions inside a macro to register them as implementations.
    If 'until' is None, it acts as the default fallback implementation.
    """

    def decorator(f: Callable):
        _macro_registrations.append((until, f))
        return f

    if func is not None:
        return decorator(func)
    return decorator


class UnresolvedMacroNode(DensityFunction):
    dispatcher: "MacroDispatcher" = dataclasses.field(repr=False, compare=False)
    args: tuple[Any, ...] = dataclasses.field(repr=False, compare=False)
    kwargs: dict[str, Any] = dataclasses.field(repr=False, compare=False)

    _cached_version: Any = dataclasses.field(init=False, default=None, repr=False, compare=False)
    _cached_node: RhombusASTNode | None = dataclasses.field(
        init=False, default=None, repr=False, compare=False
    )

    def __repr__(self) -> str:
        parts = [repr(arg) for arg in self.args]
        parts.extend(f"{k}={repr(v)}" for k, v in self.kwargs.items())
        return f"{self.dispatcher.__name__}({', '.join(parts)})"

    def resolve(self) -> RhombusASTNode:

        current_version = env.datapack_version

        if self._cached_version == current_version and self._cached_node is not None:
            return self._cached_node

        density_result = self.dispatcher._execute_for_version(*self.args, **self.kwargs)
        object.__setattr__(self, "_cached_version", current_version)

        if isinstance(density_result, Density):
            object.__setattr__(self, "_cached_node", density_result.AST)
        elif isinstance(density_result, RhombusASTNode):
            object.__setattr__(self, "_cached_node", density_result)
        else:
            raise TypeError(
                f"Macro implementation returned invalid type: {type(density_result)}"
            )

        return self._cached_node

    # Pass through standard methods to the resolved node
    def serialize_inline(self) -> Any:
        return self.resolve().serialize_inline()

    def serialize_toplevel(self) -> Any:
        return self.resolve().serialize_toplevel()

    @property
    def inscribed_toplevel_nodes(self) -> set["RhombusASTNode"]:
        return self.resolve().inscribed_toplevel_nodes


def resolve_ast(node: RhombusASTNode) -> RhombusASTNode:
    """Recursively traverses the AST and resolves all UnresolvedMacroNodes."""
    if isinstance(node, UnresolvedMacroNode):
        return resolve_ast(node.resolve())

    changes = {}
    for field_name, child_value in node.fields.items():
        if isinstance(child_value, RhombusASTNode):
            resolved_child = resolve_ast(child_value)
            if resolved_child is not child_value:
                changes[field_name] = resolved_child
        elif isinstance(child_value, list):
            new_list = []
            changed = False
            for item in child_value:
                if isinstance(item, RhombusASTNode):
                    resolved_item = resolve_ast(item)
                    new_list.append(resolved_item)
                    if resolved_item is not item:
                        changed = True
                else:
                    new_list.append(item)
            if changed:
                changes[field_name] = new_list
        elif isinstance(child_value, tuple):
            new_tuple = []
            changed = False
            for item in child_value:
                if isinstance(item, RhombusASTNode):
                    resolved_item = resolve_ast(item)
                    new_tuple.append(resolved_item)
                    if resolved_item is not item:
                        changed = True
                else:
                    new_tuple.append(item)
            if changed:
                changes[field_name] = tuple(new_tuple)

    if changes:
        # Create a new instance with the resolved children
        # We temporarily bypass the frozen check

        new_node = copy.copy(node)
        object.__setattr__(new_node, "_rhombus_frozen", False)
        for k, v in changes.items():
            object.__setattr__(new_node, k, v)
        object.__setattr__(new_node, "_rhombus_frozen", True)
        return new_node

    return node


class MacroDispatcher:
    def __init__(self, func: Callable):
        self.func = _create_argument_resolver(func)


        self.default_ns = get_module_version_namespace(func.__module__)

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
                UnresolvedMacroNode(dispatcher=self, args=args, kwargs=kwargs)
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

        for until_v, impl_func in impls:
            if until_v is None:
                if default_impl is not None:
                    raise ValueError(
                        f"Multiple default implementations (without 'until') found in macro '{self.__name__}'"
                    )
                default_impl = impl_func
            else:
                parsed_impls.append(
                    (
                        RhombusVersion(until_v, default_namespace=self.default_ns),
                        impl_func,
                    )
                )

        parsed_impls.sort(key=lambda x: x[0])

        target_v = env.datapack_version

        def _invoke(impl_f: Callable) -> Any:
            sig = inspect.signature(impl_f)
            if not sig.parameters:
                return impl_f()
            return _create_argument_resolver(impl_f)(*args, **kwargs)

        if target_v is None:
            if default_impl is None:
                raise ValueError(
                    f"No default implementation found for macro '{self.__name__}' and no target version set."
                )
            return _invoke(default_impl)

        for until_v, impl_func in parsed_impls:
            if target_v < until_v:
                return _invoke(impl_func)

        if default_impl is not None:
            return _invoke(default_impl)

        raise NotImplementedError(
            f"No valid implementation found for macro '{self.__name__}' at version {target_v}"
        )


@overload
def macro[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...
def macro(func: Callable) -> Callable:
    """The **`macro`** decorator allows functions to use the `AnyDensity` type
    for annotation of its arguments to automatically resolve passed values to
    `Density` objects.

    It acts as an organizer for `@implementation` decorated inner functions.
    """
    return cast(Callable, MacroDispatcher(func))
