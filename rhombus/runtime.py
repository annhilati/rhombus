import inspect
import functools
import copy
from typing import Final, Callable
from rhombus.core.environment import RhombusEnvironment
from rhombus.core.utils import GlobalBinding

rho: RhombusEnvironment = GlobalBinding(RhombusEnvironment)
"""The default global Rhombus environment.

For more information on how to use environments see
[RhombusEnvironment](https://annhilati.github.io/rhombus/reference/rhombus/core/environment/RhombusEnvironment/).
"""

FROM_CONTEXT: Final = object()
"""Typing sentinel to denote that a value will be adopted from the environment."""

def datapack_handler[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that handles the 'dp' parameter for datapack contexts.
    If 'dp' is FROM_CONTEXT, it injects the current env.datapack.
    If 'dp' is provided explicitly, it temporarily overrides env.datapack 
    for the duration of the function call, restoring it afterwards.
    """
    sig = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        if "dp" in bound.arguments:
            value = bound.arguments["dp"]

            if value is FROM_CONTEXT:
                bound.arguments["dp"] = rho.datapack
                return func(*bound.args, **bound.kwargs)  # type: ignore
            elif value is not rho.datapack:
                # Temporarily override the environment with the new datapack
                current_env_obj: RhombusEnvironment = rho._get_instance()
                new_env = copy.copy(current_env_obj)
                new_env.datapack = value

                token = rho._ctxvar.set(new_env)
                try:
                    return func(*bound.args, **bound.kwargs)  # type: ignore
                finally:
                    rho._ctxvar.reset(token)
            else:
                # Value is already the current environment datapack
                return func(*bound.args, **bound.kwargs)  # type: ignore
        else:
            return func(*bound.args, **bound.kwargs)  # type: ignore

    wrapper.__signature__ = sig  # type: ignore
    return wrapper
