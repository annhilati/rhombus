from typing import get_origin, get_args, Union
from types import UnionType
from Rhombus.core.density_function import DensityFunction, Reference, constant
from Rhombus.core.registry_resource import RegistryResource
from Rhombus.core.sub_parameters import SubParameters
from Rhombus.core.utils import with_datapack_context, FROM_CONTEXT
import beet, beet.contrib.worldgen as beet_worldgen

def encode[T](o: T):

    if isinstance(o, DensityFunction):
        return o.encode()
    
    elif isinstance(o, RegistryResource):
        return o.reference_identifier
    
    elif isinstance(o, SubParameters):
        return o.encode()
    
    elif isinstance(o, (list, tuple, set)):
        return type(o)(encode(m) for m in o)
    
    elif isinstance(o, dict):
        return {encode(k): encode(v) for k, v in o.items()}
    
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
    
    origin = get_origin(t)

    if origin is None:

        if t is DensityFunction:
            decode_HOLDER_HELPER_CODEC(v)

        elif issubclass(t, DensityFunction):
            return t.decode(v)
        
        elif issubclass(t, RegistryResource):
            return decode_RegistryResource_reference(v, t)
        
        elif issubclass(t, SubParameters):
            return t.decode(v)
        
        elif t in (str, float, int):
            return t(v)
        
        elif t in (list, tuple, set):
            return t(m for m in v)
            
    args = get_args(t)

    if origin in (list, tuple, set):
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
    
    return v


@with_datapack_context
def decode_RegistryResource_reference[T: RegistryResource](id: str, t: type[T], dp: beet.DataPack | None = FROM_CONTEXT) -> T:
    id = "minecraft:" + id if not ":" in id else id
    if dp is None or dp[t.fileclass].get(id, default=None) is None:
        return t.referenced(id)
    return t.decode(dp[t.fileclass][id].data)

@with_datapack_context
def decode_HOLDER_HELPER_CODEC(o: dict | str | float, dp: beet.DataPack | None = FROM_CONTEXT) -> DensityFunction:
    """Decodes any value that can be used as a HOLDER_HELPER_CODEC type argument in a density function.<br>
    (Either a JSON density function definiton, a string reference to another density function or a constant numeric value)

    Raises
    -------
    ValueError : When the dictionary has no key `'type'`
    TypeError : When no subclass of `DensityFunctionTypeBase` is defined, that has it's attribute `id` equal to `o["type"]` and thus, it is not known how to decode the dictionary
    """

    # `HOLDER_HELPER_CODEC` is a term used in the density function codebase for handling arguments,
    # that can either be a constant number, a reference to another density function, or a fully defined inline density function.<br>
    # There are other codecs for that too (see `clamp`), but for clarity and supportiveness we will only use this one.

    if isinstance(o, dict):
        t: str | None = o.get("type")
        if t is None:
            raise ValueError("Cannot decode dict as HOLDER_HELPER_CODEC argument without key 'type'")
        if ":" not in t:
            t = "minecraft:" + t
        cls = DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES.get(t)
        if cls is None:
            raise TypeError(
                f"Cannot decode dict as HOLDER_HELPER_CODEC argument with type id '{t}'. "
                "No density function class with adequate id is defined"
            )
        return cls.decode(o)

    elif isinstance(o, (int, float)):
        return constant(float(o))

    elif isinstance(o, str):
        o = "minecraft:" + o if ":" not in o else o

        default = None
        if dp is not None and (f := dp[beet_worldgen.WorldgenDensityFunction].get(o)) is not None:
            default = f.data
        return Reference(o, default=decode_HOLDER_HELPER_CODEC(default) if default is not None else None)

    else:
        raise TypeError(f"Cannot decode type '{type(o).__name__}' as HOLDER_HELPER_CODEC argument")
