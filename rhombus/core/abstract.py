from typing import Any, Self, Callable, Protocol, get_type_hints, get_args
import inspect
import functools

from rhombus.core.environment import (
    _parse_version_specifier,
    get_module_addon_namespace,
    DatapackVersion,
    VersionString,
    VersionTuple
)
from rhombus.runtime import rho

__all__ = [
    "RhombusASTNode",
    "LazyDispatcher",
    "implementation",
    "RhombusAbstractType",
]


class RhombusASTNode[T]:
    """Represents a lazy, unresolved node in the abstract syntax tree."""
    
    def __init__(
        self,
        dispatcher: Callable[..., Any],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        repr_func: Callable[[Self], str] | None = None,
    ):
        self.dispatcher = dispatcher
        self.args = args
        self.kwargs = kwargs or {}
        self.repr_func = repr_func

        self._cached_version: Any = None
        self._cached_node: T | None = None

    @classmethod
    def defer[R](
        cls,
        func: Callable[[], R],
        # *args: Any,
        repr_func: Callable[["RhombusASTNode[R]"], str] | None = None,
        # **kwargs: Any,
    ) -> "RhombusASTNode[R]":
        # TODO: Can we safely remove the argument parameters? I believe we need them because using
        #       lambdas makes comparing RhombusASTNodes impossible, because every call of the lambda-
        #       keyword creates a new object. 
        target_cls = cls
        if getattr(cls, "__parameters__", None):
            return_type = None
            try:
                hints = get_type_hints(func)
                return_type = hints.get("return")
            except Exception:
                return_type = getattr(func, "__annotations__", {}).get("return")
                if return_type is None:
                    try:
                        sig = inspect.signature(func)
                        if sig.return_annotation is not inspect.Signature.empty:
                            return_type = sig.return_annotation
                    except Exception:
                        pass

            if return_type is not None and return_type is not Any:
                try:
                    target_cls = cls[return_type]
                except Exception:
                    pass

        return target_cls(func, repr_func=repr_func)
        #                       args=args, kwargs=kwargs

    @classmethod
    def value[T](cls, val: T) -> "RhombusASTNode[T]":
        """Create a RhombusASTNode that simply contains a value when no lazy execution is needed."""

        def identity():
            # This function is required instead of a lambda to enable correct comparison of simple RhombusASTNodes.
            return val

        repr: Callable[[RhombusASTNode, str]] = (
            lambda n: val.__repr__()
        )
        return cls.defer(identity, repr_func=repr)

    @property
    def return_type(self) -> Any:
        orig = getattr(self, "__orig_class__", None)
        if orig is not None:
            args = get_args(orig)
            if args:
                return args[0]
        if hasattr(self, "dispatcher"):
            try:
                hints = get_type_hints(self.dispatcher)
                ret = hints.get("return")
                if ret is not None and ret is not Any:
                    return ret
            except Exception:
                ret = getattr(self.dispatcher, "__annotations__", {}).get("return")
                if ret is not None and ret is not Any:
                    return ret
        return Any

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
        name = getattr(self.dispatcher, "__name__", getattr(type(self.dispatcher), "__name__", "lazy"))
        return f"{name}({', '.join(parts)})"

    def build(self) -> T:
        current_version = rho.datapack_version

        if self._cached_version == current_version and self._cached_node is not None:
            return self._cached_node

        if hasattr(self.dispatcher, "_execute_for_version"):
            result = self.dispatcher._execute_for_version(*self.args, **self.kwargs) # type: ignore
        else:
            result = self.dispatcher(*self.args, **self.kwargs)

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



class LazyDispatcher:
    def __init__(self, func: Callable, repr_func: Callable | None = None):
        self.func = func
        self.repr_func = repr_func
        self.default_ns = get_module_addon_namespace(func.__module__) or "datapack"
        functools.update_wrapper(self, func)
        self.__signature__ = inspect.signature(func)

    def __get__(self, instance: Any, owner: Any = None) -> Any:
        if instance is None:
            return self
        return functools.partial(self, instance)

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


_macro_registrations: list[
    tuple[
        DatapackVersion | VersionString | VersionTuple | tuple[str, DatapackVersion | VersionString | VersionTuple],
        DatapackVersion | VersionString | VersionTuple | tuple[str, DatapackVersion | VersionString | VersionTuple],
        Callable
    ]
] = []


def implementation(
    func: Callable | None = None, 
    *, 
    since=None,
    until=None
):
    """Decorator for inner functions inside a macro to register them as version implementations."""
    # TODO: Rationalize; this should probably be a fabric and not a decorator here
    def decorator(f: Callable):
        _macro_registrations.append((since, until, f))
        return f

    if func is not None:
        return decorator(func)
    return decorator


class RhombusAbstractType[T](Protocol):
    AST: RhombusASTNode[T]