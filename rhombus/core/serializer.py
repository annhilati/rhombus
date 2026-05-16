from typing import get_origin, get_args, Union, TypeAliasType, Literal, Any
from types import UnionType
from rhombus.core.utils import contextfunction, FROM_CONTEXT, JSONValue
from rhombus.core.node import RhombusASTNode, SerializationContext
from rhombus import config
import beet

__all__ = ["serialize", "deserialize"]


def serialize[T](o: T, ctx: SerializationContext) -> JSONValue | T:
    "Main serialization function"

    if isinstance(o, RhombusASTNode):
        return o.serialize(ctx)
    
    elif isinstance(o, (list, tuple)):
        return type(o)(serialize(m, ctx) for m in o)
    
    elif isinstance(o, dict):
        return {serialize(k, ctx): serialize(v, ctx) for k, v in o.items()}
    
    return o

@classmethod
@contextfunction(dp=config.ctx.datapack)
def deserialize[T](v: Any, t: type[T], ctx: SerializationContext, dp: beet.DataPack | None = FROM_CONTEXT) -> T:
    "Main deserialization function"
    
    origin = get_origin(t)

    if origin is None:

        if issubclass(t, RhombusASTNode):
            return t.deserialize(v, ctx, dp)
        
        elif t in (str, float, int, Literal):
            return t(v)
        
        elif t in (list, tuple, set):
            return t(m for m in v)
        
        elif isinstance(t, TypeAliasType):
            return deserialize(v, t.__value__)
            
    args = get_args(t)
    
    if origin is Literal:
            return str(v)

    elif origin in (list, tuple, set):
        return t(
            deserialize(m, args[0] if len(args) == 1 else Union[*args]) for m in v
        )
    
    elif origin in (Union, UnionType):
        if type(v) in args:
            return deserialize(v, type(v))
        for arg in args:
            try:
                return deserialize(v, arg)
            except:
                continue

    elif origin is dict:
        kt, vt = args
        return {
            deserialize(k, kt): deserialize(v, vt)
            for k, v in v.items()
        }
    
    raise ValueError(f"No deserialization procedure for target type '{t.__name__}' known")


# @contextfunction(dp=config.ctx.datapack)
# def resolve_DatapackResource_reference[T: DatapackResource](id: str, t: type[T], dp: beet.DataPack | None = FROM_CONTEXT) -> T:
#     id = "minecraft:" + id if not ":" in id else id
#     if dp is not None and (file := dp[t.fileclass].get(id)) is not None:
#         return t.deserialize(file.data)
#     return t.referenced(id)

# @contextfunction(dp=config.ctx.datapack)
# def decode_HOLDER_HELPER_CODEC(o: dict | str | float, dp: beet.DataPack | None = FROM_CONTEXT) -> DensityFunction:
#     """Decodes any value that can be used as a HOLDER_HELPER_CODEC type argument in a density function.<br>
#     (Either a JSON density function definiton, a string reference to another density function or a constant numeric value)

#     Raises
#     -------
#     ValueError : When the dictionary has no key `'type'`
#     TypeError : When no subclass of `DensityFunctionTypeBase` is defined, that has it's attribute `id` equal to `o["type"]` and thus, it is not known how to decode the dictionary
#     """

#     # `HOLDER_HELPER_CODEC` is a term used in the density function codebase for handling arguments,
#     # that can either be a constant number, a reference to another density function, or a fully defined inline density function.<br>
#     # There are other codecs for that too (see `clamp`), but for clarity and supportiveness we will only use this one.

#     if isinstance(o, dict):
#         t: str | None = o.get("type")
#         if t is None:
#             raise ValueError("Cannot decode dict as HOLDER_HELPER_CODEC argument without key 'type'")
#         if ":" not in t:
#             t = "minecraft:" + t
#         cls = DensityFunction.REGISTERED_DENSITY_FUNCTION_TYPES.get(t)
#         if cls is None:
#             raise TypeError(
#                 f"Cannot decode dict as HOLDER_HELPER_CODEC argument with type id '{t}'. "
#                 "No density function class with adequate id is defined"
#             )
#         return cls.deserialize(o)

#     elif isinstance(o, (int, float)):
#         return constant(float(o))

#     elif isinstance(o, str):
#         o = "minecraft:" + o if ":" not in o else o

#         default = None
#         if dp is not None and (f := dp[beet_worldgen.WorldgenDensityFunction].get(o)) is not None:
#             default = f.data
#         return Reference(o, definition=decode_HOLDER_HELPER_CODEC(default) if default is not None else None)

#     else:
#         raise TypeError(f"Cannot decode type '{type(o).__name__}' as HOLDER_HELPER_CODEC argument")
