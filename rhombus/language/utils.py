from typing import Union, TypeAliasType, Callable, get_args, get_origin
from types import UnionType
from rhombus import config
from rhombus.language import Density, types
from rhombus.core import DensityFunction, constant, Reference
from rhombus.core.utils import Decorator
import inspect, functools

type DensityDescriptor = Union[Density, DensityFunction, str, float]
"TypeAliasType for all types that can be interpreted by `resolve_DensityDescriptor()`."

def resolve_DensityDescriptor(arg: DensityDescriptor) -> Density:
    """Interprets a QoL argument input and returns a Density object.
    Applies logic like splitting large literal constants into calculations
    before constructing constant AST nodes.
    """

    limit = config.constant_number_limit

    if isinstance(arg, (int, float)):
        v = float(arg)

        if abs(v) <= limit:
            return Density(constant(v))

        sign = -1.0 if v < 0 else 1.0
        v = abs(v)

        factors: list[float] = []
        while v > limit:
            factors.append(float(limit))
            v /= limit

        factors.append(v * sign)

        it = iter(constant(f) for f in factors)
        result = types.mul(next(it), next(it))
        for x in it:
            result = types.mul(result, x)

        return Density(result)

    if isinstance(arg, Density):
        return arg

    if isinstance(arg, DensityFunction):
        return Density(arg)

    if isinstance(arg, str):
        if ":" not in arg:
            arg = "minecraft:" + arg
        return Density(Reference(arg))

    raise ValueError(f"Cannot resolve object of type '{type(arg)}' to a density function")


def WizardFactory(*, unwrap: bool = False) -> Decorator:
    
    def _apply_by_annotation(annotation: type) -> bool:
        if annotation is DensityDescriptor:
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
                    resolved = resolve_DensityDescriptor(current_val)

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
        from rhombus.language.utils import WizardFactory
        self._wrapped = WizardFactory(unwrap=False)(fn)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self._wrapped(*args, **kwargs)


class builtinmacro[**P, R]:
    """Shortcut for WizardFactory(unwrap=True)"""

    def __init__(self, fn: Callable[P, R]):
        from rhombus.language.utils import WizardFactory
        self._wrapped = WizardFactory(unwrap=True)(fn)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self._wrapped(*args, **kwargs)
