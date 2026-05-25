"""
DSL types are a special kind of typing types that come with tooling for automatic parsing of arguments in functions.

Essentially, they are like typing with Unions, but:
1. with the help of a decorator, functions where a DSLtype is used in a annotation, the argument value will be unified in a way defined by the user
2. IDE will display only unify types attributes

"""

from typing import Callable, Any, get_args, get_origin, get_type_hints, overload, Union
import functools, inspect, types, sys

class DSLTypeMeta(type):

    @property
    def _dsl_result_type(cls) -> type | None:
        "Returns the type used in the DSLType for attribute suggestions. During the registration of generic classes, None can be returned."
        from typing import Generic, get_origin
        
        bases = type.__getattribute__(cls, "__bases__")
        
        for base in bases:
            if base.__name__ == "DSLType":
                continue
            if base is Generic or get_origin(base) is Generic:
                continue                
            return base
            
        return None

    def __getattribute__(cls, name: str):

        if name.startswith("__"):
            return type.__getattribute__(cls, name)

        if name in ("_dsl_result_type", "unify"):
            return type.__getattribute__(cls, name)
        
        res_type = cls._dsl_result_type
        
        if res_type is not None:

            if name in dir(res_type) and name not in cls.__dict__:
                raise AttributeError(
                    f"Forbidden access: '{name}' belongs to the underlying type '{res_type.__name__}' "
                    f"and cannot be accessed via the DSLType '{cls.__name__}'."
                )
            
        return type.__getattribute__(cls, name)


class DSLType(metaclass=DSLTypeMeta):
    """DSLTypes are typing types that can be used to unify values of arguments
    annotated with such a type.  
    Unlike unions (that are used for similar purposes), DSLTypes feature IDE
    suggestions for only one type (the type values get unified to).
    
    ## Usage
    ```
    class number(DSLType, float):
    
        @classmethod
        def unify(cls, v: int | float | str, *, kwarg, **kwargs) -> float:
            return float(v)
    ```
    
    ### `unify` Method
    This method defines how values of annotated arguments are unified.  
    The method is a `classmethod`, takes the implicit `cls` argument, one
    positional argument, any named keyword arguments and **must contain
    the variadic keyword arguments**.
    The result type should always be the same as the second class argument of
    the class (raising exceptions is permitted and preferred over returning
    `None`).
    
    When using `cls.unify()` recursively in your definition, make sure to pass
    along all arguments.
    """
    
    @classmethod
    def unify[V, T](cls, v: V, **kwargs) -> T:
        raise NotImplementedError
    
    def __new__(cls, *args, **kwargs):
        raise TypeError("DSLType classes cannot be instanciated")
    
    #======// Definition Validation //===========================================================//
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        if cls.__name__ == "DSLType":
            return
        
        #======// Class Arguments //=====================//
        
        try:
            if not isinstance(cls._dsl_result_type, type):
                raise TypeError
        except (AttributeError, IndexError, TypeError):
            raise TypeError(f"The second class argument of DSLType '{cls.__name__}' must be a valid type.")
        
        #======// Unify Method Requirements //===========//

        unbound_unify = cls.__dict__.get('unify')
        
        if not isinstance(unbound_unify, classmethod):
            raise TypeError(f"Method '{cls.__name__}.unify' must be decorated with @classmethod.")

        sig = inspect.signature(unbound_unify.__func__)
        params = list(sig.parameters.values())

        if len(params) < 3:
            raise TypeError(
                f"Method '{cls.__name__}.unify' must accept at least 3 arguments: "
                f"(cls, v, **kwargs). Currently: {[p.name for p in params]}"
            )

        if params[0].name not in ("cls", "self"):
            pass 
        if params[1].kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY):
            raise TypeError(f"The second argument of '{cls.__name__}.unify' must be the positional argument to unify.")
        if params[-1].kind != inspect.Parameter.VAR_KEYWORD:
            raise TypeError(f"Method '{cls.__name__}.unify' must accept variadic keyword arguments (**kwargs) at the end.")
        for i in range(2, len(params) - 1):
            if params[i].kind != inspect.Parameter.KEYWORD_ONLY:
                raise TypeError(f"Extra argument '{params[i].name}' in '{cls.__name__}.unify' must be keyword-only (after a '*').")
        hints = get_type_hints(unbound_unify.__func__)
        if hints.get("return") is not cls._dsl_result_type:
            raise TypeError(f"The result type of '{cls.__name__}.unify' must match the underlying type of '{cls.__name__}' which is '{cls._dsl_result_type.__name__}'")

        #======// Unify Method Definition //=============//

        try:
            cls.unify(0)
        except NotImplementedError:
            raise TypeError(f"DSLType '{cls.__name__}' must implement a working 'unify' method.")
        except Exception:
            pass # Other exceptions (because of missing kwargs) are fine for the test call
    
    
# ╭───────────────────────────────────────────────────────────────────────────────╮
# │                                   Decorator                                   │ 
# ╰───────────────────────────────────────────────────────────────────────────────╯
    
class DSLMethod:
    """Use this decorator on functions to automatically resolve arguments
    annotated with a `DSLType`.
    
    Supported nested types are:
    - `list`, `set`, `tuple` (fixed and variadic)
    - `dict`
    - `Union`, `UnionType`: The first applicable DSLType will be used for
        unification. If they all fail, the first will raise it's exception
    
    ## Usage
    In most cases, you will want to implement your own decorator for such
    functions (for example, a helper for defining macros, handling context,
    etc.), and use this decorator there. This is especially helpful
    if you want your decorator to display specific keyword arguments. The
    DSLMethod decorator can accept these and pass them along to every call of
    `~.unify()` of `DSLType` subclasses when resolving the arguments.
    """
    # TODO: Also implement support for *args
    @overload # Usage without paratheses (@Decorator)
    def __new__[**P, R](cls, func: Callable[P, R]) -> Callable[P, R]: ...
    @overload # Usage with parentheses (@Decorator(key=...))
    def __new__(cls, func: None = None, **kwargs: Any) -> "DSLMethod": ...

    def __new__(cls, func=None, **kwargs):
        if callable(func) and not kwargs:
            return cls._make_wrapper(func, {})
        return super().__new__(cls)

    def __init__(self, func=None, **kwargs):
        self.kwargs = kwargs

    def __call__[**P, R](self, func: Callable[P, R]) -> Callable[P, R]:
        # Benutzung mit Klammern: Die Instanz wird auf die Funktion aufgerufen
        return self._make_wrapper(func, self.kwargs)

    @staticmethod
    def _make_wrapper[**P, R](func: Callable[P, R], deco_kwargs: dict[str, Any]) -> Callable[P, R]:
        sig = inspect.signature(func)
        module = sys.modules[func.__module__]

        hints = get_type_hints(
            func,
            globalns=module.__dict__,
        )

        def parse_value(val: Any, hint: Any) -> Any:

            origin = get_origin(hint)
            args = get_args(hint)

            # 1. Handle Union Types (e.g. int | DSLType oder Union[int, str])
            if origin is Union or isinstance(hint, types.UnionType):
                first_exception = None
                for arg in args:
                    try:
                        return parse_value(val, arg)
                    except Exception as e:
                        if first_exception is None:
                            first_exception = e
                
                if first_exception:
                    raise first_exception
                return val

            # 2. Handle DSLType subclasses
            if isinstance(hint, type) and issubclass(hint, DSLType):
                return hint.unify(val, **deco_kwargs)

            # 3. Recursive container check
            try:
                if origin is list and args:
                    return [parse_value(v, args[0]) for v in val]
                
                if origin is set and args:
                    return {parse_value(v, args[0]) for v in val}
                
                if origin is tuple and args:
                    # Variadic tupel: tuple[T, ...]
                    if len(args) == 2 and args[1] is Ellipsis:
                        return tuple(parse_value(v, args[0]) for v in val)
                    # Fixed tupel: tuple[T1, T2]
                    return tuple(parse_value(v, a) for v, a in zip(val, args))
                
                if origin is dict and args:
                    k_hint, v_hint = args
                    return {parse_value(k, k_hint): parse_value(v, v_hint) for k, v in val.items()}
            
            except (TypeError): # If val is not iterable, even if the hint says it is
                return val

            return val

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            for name, value in bound.arguments.items():
                if name in hints:

                    bound.arguments[name] = parse_value(value, hints[name])

            return func(*bound.args, **bound.kwargs)

        return wrapper