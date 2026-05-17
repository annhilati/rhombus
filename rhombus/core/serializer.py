from typing import get_origin, get_args, Union, TypeAliasType, Literal, Any
from types import UnionType

import beet

from rhombus.core.utils import contextfunction, FROM_CONTEXT, JSONValue
from rhombus.core.node import RhombusASTNode
from rhombus import config

__all__ = ["serialize_any", "deserialize_any"]  


def serialize_any[T](o: T, inline: bool = True) -> JSONValue | T:
    "Main serialization function"

    if isinstance(o, RhombusASTNode):   
        return o.serialize(inline=inline)
    
    elif isinstance(o, (list, tuple)):
        return type(o)(serialize_any(m) for m in o)
    
    elif isinstance(o, dict):
        return {serialize_any(k): serialize_any(v) for k, v in o.items()}
    
    return o

@contextfunction(dp=config.ctx.datapack)
def deserialize_any[T](v: Any, t: type[T], inline: bool = True, dp: beet.DataPack | None = FROM_CONTEXT) -> T:
    "Main deserialization function for when the targettet type is known"
    
    origin = get_origin(t)

    if origin is None:

        if issubclass(t, RhombusASTNode):
            return t.deserialize(data=v, dp=dp, inline=inline)
        
        elif t in (str, float, int, Literal):
            return t(v)
        
        elif t in (list, tuple, set):
            return t(m for m in v)
        
        elif isinstance(t, TypeAliasType):
            return deserialize_any(v, t.__value__)
            
    args = get_args(t)
    
    if origin is Literal:
            return str(v)

    elif origin in (list, tuple, set):
        return t(
            deserialize_any(m, Union[*args]) for m in v
        )
    
    elif origin in (Union, UnionType):
        if type(v) in args:
            return deserialize_any(v, type(v))
        for arg in args:
            try:
                return deserialize_any(v, arg)
            except:
                continue

    elif origin is dict:
        kt, vt = args
        return {
            deserialize_any(k, kt): deserialize_any(v, vt)
            for k, v in v.items()
        }
    
    raise ValueError(f"No deserialization procedure for target type '{t.__name__}' known")