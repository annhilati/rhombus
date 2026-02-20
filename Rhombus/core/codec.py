from typing import get_origin, get_args, Union
from types import UnionType

def encode[T](o: T):
    from Rhombus.core.density_function import DensityFunction
    from Rhombus.core.registry_resource import RegistryResource
    from Rhombus.core.params import SubParameters

    if isinstance(o, DensityFunction):
        return o.encode()
    
    elif isinstance(o, RegistryResource):
        return o.encode()
    
    elif isinstance(o, SubParameters):
        return o.encode()
    
    elif isinstance(o, (list, tuple)):
        return type(o)(encode(m) for m in o)
    
    return o

def decode[V, T](v: V, t: type[T]) -> T:
    """Casts a value `v` into a type `t` according to specific procedures.
    
    Supported are:
    - `DensityFunction` subclasses
    - `RegistryResource` subclasses
    - `SubParameters` subclasses
    - `str`, `int`, `float`
    - `list[T]`, `tuple[T]`
    - `dict[KT, VT]`
    - `Union[T]`, `UnionType[T]`
    """
        
    from Rhombus.core.density_function import DensityFunction
    from Rhombus.core.registry_resource import RegistryResource
    from Rhombus.core.params import SubParameters
    
    origin = get_origin(t)

    if origin is None:

        if issubclass(t, DensityFunction):
            return t.decode(v)
        
        elif issubclass(t, RegistryResource):
            return t.decode(v)
        
        elif issubclass(t, SubParameters):
            return t.decode(v)
        
        elif t in (str, float, int):
            return t(v)
        
        elif t in (list, tuple):
            return t(m for m in v)
            
    args = get_args(t)

    if origin in (list, tuple):
        return t(
            decode(m, args[0] if len(args) == 1 else Union[*args]) for m in v
        )
    
    if origin in (Union, UnionType):
        if type(v) in args:
            return decode(v, type(v))
        for arg in args:
            try:
                return decode(v, arg)
            except:
                continue

    if origin is dict:
        kt, vt = args
        return {
            decode(k, kt): decode(v, vt)
            for k, v in v.items()
        }
    
    raise