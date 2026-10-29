from typing import Any, Optional, Self, Callable, Protocol, get_type_hints, get_args
from types import EllipsisType
import inspect
import functools
import copy

from rhombus.core.environment import (
    DatapackVersion,
    VersionString,
    VersionTuple,
    get_module_extension_namespace,
    parse_version_specifier,
)
from rhombus.core.models import DatapackNode
from rhombus.runtime import rho

__all__ = [
    "RhombusASTNode",
    "LazyDispatcher",
    "register_implementation",
    "has_implementation_registrations",
    "RhombusAbstractType",
]


class RhombusASTNode[T]:
    """The **`RhombusASTNode`** type is a wrapper for producing values in a lazy manner.
    """
    _value: T | EllipsisType = ... # we use this for some cases where the result is effectively known to ensure proper comparability
    
    def __init__(
        self,
        dispatcher: "LazyDispatcher" | Callable[..., T],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] = {},
        repr: Callable[[Self], str] | None = None,
    ):
        self.dispatcher = dispatcher
        self.args = args
        self.kwargs = kwargs
        self.repr_func = repr

        self._cached_version: DatapackVersion = None
        self._cached_node: T | None = None

    @classmethod
    def defer[T](
        cls,
        fabric: Callable[[], T],
        repr: Optional[Callable[[Self], str]] = None,
    ) -> "RhombusASTNode[T]":
        """Creates a `RhombusASTNode` that lazily produces a value from a fabric."""

        target_cls = cls
        if getattr(cls, "__parameters__", None):
            return_type = None
            try:
                hints = get_type_hints(fabric)
                return_type = hints.get("return")
            except Exception:
                return_type = getattr(fabric, "__annotations__", {}).get("return")
                if return_type is None:
                    try:
                        sig = inspect.signature(fabric)
                        if sig.return_annotation is not inspect.Signature.empty:
                            return_type = sig.return_annotation
                    except Exception:
                        pass

            if return_type is not None and return_type is not Any:
                try:
                    target_cls = cls[return_type]
                except Exception:
                    pass

        return target_cls(fabric, repr=repr)


    @classmethod
    def value[T](cls, val: T) -> "RhombusASTNode[T]":
        """Creates a `RhombusASTNode` that simply contains a value when no lazy execution is needed."""

        def identity():
            return val

        repr: Callable[[RhombusASTNode], str] = (
            lambda n: val.__repr__()
        )
        node = cls.defer(identity, repr=repr)
        node._value = val
        return node

    @property
    def return_type(self) -> type[T]:
        orig = getattr(self, "__orig_class__", None)
        if orig is not None:
            args = get_args(orig)
            if args:
                return args[0]
        try:
            hints = get_type_hints(self.dispatcher)
            ret = hints.get("return")
            if ret is not None and ret is not Any:
                return ret
        except Exception:
            ret = getattr(self.dispatcher, "__annotations__", {}).get("return")
            if ret is not None and ret is not Any:
                return ret

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RhombusASTNode):
            return False
        if self._value is not ... and other._value is not ...:
            return self._value == other._value
        return (
            self.dispatcher == other.dispatcher
            and self.args == other.args
            and self.kwargs == other.kwargs
        )

    def __hash__(self) -> int:
        if self._value is not ...:
            return hash(self._value)
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

        if isinstance(self.dispatcher, LazyDispatcher):
            result = self.dispatcher._execute_for_version(*self.args, **self.kwargs) # type: ignore
        else:
            result = self.dispatcher(*self.args, **self.kwargs)

        def _deep_build(node: Any) -> Any:
            if isinstance(node, RhombusASTNode):
                return node.build()
            
            if isinstance(node, DatapackNode):
                changes = {}
                for field_name, child_value in node.fields.items():
                    new_child_value = _deep_build(child_value)
                    if new_child_value is not child_value:
                        changes[field_name] = new_child_value

                if changes:
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
        self.default_ns = get_module_extension_namespace(func.__module__) or "datapack"
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
            repr=self.repr_func
        )

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, LazyDispatcher):
            return self.func == other.func
        return False

    def __hash__(self) -> int:
        return hash(self.func)

    def _execute_for_version(self, *args: Any, **kwargs: Any) -> Any:
        _implementation_registrations.clear()

        result = self.func(*args, **kwargs)

        impls = list(_implementation_registrations)
        _implementation_registrations.clear()

        if not impls:
            return result

        parsed_impls = []
        default_impl = None

        def _parse_impl_spec(v: Any) -> tuple[str, VersionTuple] | None:
            if v is None:
                return None
            if isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], (str, int, float, tuple)):
                ns, ver = v[0], v[1]
            else:
                ns, ver = self.default_ns, v
            is_dp = (ns == "datapack")
            return (ns, parse_version_specifier(ver, interpret_as_game_version_convert_to_datapack_version=is_dp))

        for since_v, until_v, impl_func in impls:
            p_since = _parse_impl_spec(since_v)
            p_until = _parse_impl_spec(until_v)
            
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
            return rho._check_version(req_v, namespace=ns) is True

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


_implementation_registrations: list[
    tuple[
        DatapackVersion | VersionString | VersionTuple | None,
        DatapackVersion | VersionString | VersionTuple | None,
        Callable
    ]
] = []


def register_implementation(
    func: Callable, 
    *, 
    since: DatapackVersion | VersionString | VersionTuple | None = None,
    until: DatapackVersion | VersionString | VersionTuple | None = None
) -> None:
    _implementation_registrations.append((since, until, func))


def has_implementation_registrations() -> bool:
    return len(_implementation_registrations) > 0


class RhombusAbstractType[T](Protocol):
    AST: RhombusASTNode[T]