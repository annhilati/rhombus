import inspect, functools
from typing import Callable

from rhombus.core.dsl.DSLType import DSLMethod
from rhombus.core.utils import Decorator

__all__ = ["macro"]


def macro[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    """Decorator to help with building macros. Macros are functions that return a `Density` object.
    
    When the macro is called any parameters annotated with `AnyDensity` will be
    resolved to `Density` objects. Then, the arguments can savely be used in builtin
    factories or other macros.

    Builtin factories that use this decorator should alway pass the `~.AST` attribute
    of the resolved arguments, because `Density` itself is not a valid node type.
    """

    def decorator[**P, R](func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)
        
        # Apply DSLMethod to the whole function instead of manually unifying
        decorated = DSLMethod(func)
        try:
            functools.wraps(func)(decorated)
        except Exception:
            # if DSLMethod returns a callable object that isn't a function,
            # functools.wraps may fail; ignore in that case
            pass
        # Preserve original signature for tooling/inspection
        decorated.__signature__ = sig
        return decorated

    return decorator(fn)