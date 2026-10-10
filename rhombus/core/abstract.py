from typing import Any, Callable, overload, cast
import inspect
import functools

from rhombus.core.environment import _parse_version_specifier, get_module_addon_namespace
from rhombus.runtime import rho


class RhombusASTNode[T]:
    """Represents a lazy, unresolved node in the abstract syntax tree."""
    
    def __init__(self, dispatcher: "LazyDispatcher", args: tuple[Any, ...], kwargs: dict[str, Any], repr_func: Callable | None = None):
        self.dispatcher = dispatcher
        self.args = args
        self.kwargs = kwargs
        self.repr_func = repr_func

        self._cached_version: Any = None
        self._cached_node: T | None = None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RhombusASTNode):
            return False
        return (
            self.dispatcher == other.dispatcher
            and self.args == other.args
            and self.kwargs == other.kwargs
        )

    def __hash__(self) -> int:
        return hash((
            self.dispatcher,
            self.args,
            frozenset(self.kwargs.items())
        ))

    def __repr__(self) -> str:
        if self.repr_func is not None:
            return self.repr_func(self)
        parts = [repr(arg) for arg in self.args]
        parts.extend(f"{k}={repr(v)}" for k, v in self.kwargs.items())
        return f"{self.dispatcher.__name__}({', '.join(parts)})"

    def build(self) -> T:
        current_version = rho.datapack_version

        if self._cached_version == current_version and self._cached_node is not None:
            return self._cached_node

        result = self.dispatcher._execute_for_version(*self.args, **self.kwargs) # type: ignore

        def _deep_build(node: Any) -> Any:
            if isinstance(node, RhombusASTNode):
                return node.build()
            
            if hasattr(node, "fields") and isinstance(node.fields, dict):
                changes = {}
                for field_name, child_value in node.fields.items():
                    new_child_value = _deep_build(child_value)
                    if new_child_value is not child_value:
                        changes[field_name] = new_child_value

                if changes:
                    import copy
                    new_node = copy.copy(node)
                    object.__setattr__(new_node, "_rhombus_frozen", False)
                    for k, v in changes.items():
                        object.__setattr__(new_node, k, v)
                    object.__setattr__(new_node, "_rhombus_frozen", True)
                    node = new_node
                return node
                
            if isinstance(node, list):
                new_list = [_deep_build(item) for item in node]
                return new_list if new_list != node else node
            if isinstance(node, tuple):
                new_tuple = tuple(_deep_build(item) for item in node)
                return new_tuple if new_tuple != node else node
            if isinstance(node, dict):
                new_dict = {_deep_build(k): _deep_build(v) for k, v in node.items()}
                return new_dict if new_dict != node else node
            if isinstance(node, set):
                new_set = {_deep_build(item) for item in node}
                return new_set if new_set != node else node
            if isinstance(node, frozenset):
                new_frozenset = frozenset(_deep_build(item) for item in node)
                return new_frozenset if new_frozenset != node else node

            return node

        result = _deep_build(result)

        self._cached_version = current_version
        self._cached_node = result
        return self._cached_node


_macro_registrations: list[tuple[Any, Any, Callable]] = []


def implementation(
    func: Callable | None = None, 
    *, 
    since=None,
    until=None
):
    """Decorator for inner functions inside a macro to register them as version implementations."""
    def decorator(f: Callable):
        _macro_registrations.append((since, until, f))
        return f

    if func is not None:
        return decorator(func)
    return decorator


class LazyDispatcher:
    def __init__(self, func: Callable, repr_func: Callable | None = None):
        self.func = func
        self.repr_func = repr_func
        self.default_ns = get_module_addon_namespace(func.__module__) or "datapack"
        functools.update_wrapper(self, func)
        self.__signature__ = inspect.signature(func)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.__signature__.bind(*args, **kwargs)
        return RhombusASTNode(
            dispatcher=self,
            args=args,
            kwargs=kwargs,
            repr_func=self.repr_func
        )

    def _execute_for_version(self, *args: Any, **kwargs: Any) -> Any:
        global _macro_registrations
        _macro_registrations = []

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
                        f"Multiple default implementations found in macro '{self.__name__}'"
                    )
                default_impl = impl_func
            else:
                parsed_impls.append((p_since, p_until, impl_func))

        def _invoke(impl_f: Callable) -> Any:
            sig = inspect.signature(impl_f)
            if not sig.parameters:
                return impl_f()
            return impl_f(*args, **kwargs)

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
            return _invoke(valid_impls[-1])

        if default_impl is not None:
            return _invoke(default_impl)

        raise NotImplementedError(
            f"No implementation found for macro '{self.__name__}' for versions: {rho.versions}."
        )


@overload
def lazy[**P, R](func: Callable[P, R]) -> Callable[P, RhombusASTNode[R]]: ...
@overload
def lazy[**P, R](*, repr: Callable[["RhombusASTNode"], str] | None = None) -> Callable[[Callable[P, R]], Callable[P, RhombusASTNode[R]]]: ...
def lazy(
    func: Callable | None = None,
    *,
    repr: Callable[["RhombusASTNode"], str] | None = None
) -> Callable:
    def decorator(f: Callable) -> Callable:
        return cast(Callable, LazyDispatcher(f, repr_func=repr))
    
    if func is not None:
        return decorator(func)
    return decorator