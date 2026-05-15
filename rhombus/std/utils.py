from typing import Union, TypeAliasType, Callable, get_args, get_origin
from types import UnionType
from rhombus.core.utils import Decorator
from rhombus.core.dsl.DSLType import DSLMethod
from rhombus.std.density import Density, densityfunction
import inspect, functools

def WizardFactory(*, unwrap: bool = False) -> Decorator:
    
    def _apply_by_annotation(annotation: type) -> bool:
        if annotation is densityfunction:
            return True
        if get_origin(annotation) in [Union, UnionType]:
            args = get_args(annotation)
            if Density in args and any([t in args for t in [str, float, int]]):
                return True
        if isinstance(annotation, TypeAliasType):
            return _apply_by_annotation(annotation.__value__)
        return False

    def decorator[**P, R](func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)
        
        params_to_resolve = {
            name for name, param in sig.parameters.items()
            if _apply_by_annotation(param.annotation)
        }

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            for name in params_to_resolve:
                if name in bound.arguments:
                    current_val = bound.arguments[name]
                    resolved = densityfunction.unify(current_val)
                    # replace this with DSLmethod logic sometime

                    if unwrap:
                        bound.arguments[name] = resolved.AST
                    else:
                        bound.arguments[name] = resolved

            return func(*bound.args, **bound.kwargs)

        wrapper.__signature__ = sig
        return wrapper

    return decorator


class macro[**P, R]:
    """Shortcut for WizardFactory(unwrap=False)"""

    def __init__(self, fn: Callable[P, R]):
        self._wrapped = WizardFactory(unwrap=False)(fn)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self._wrapped(*args, **kwargs)


class builtinmacro[**P, R]:
    """Shortcut for WizardFactory(unwrap=True)"""

    def __init__(self, fn: Callable[P, R]):
        self._wrapped = WizardFactory(unwrap=True)(fn)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self._wrapped(*args, **kwargs)
