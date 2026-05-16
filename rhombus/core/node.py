from typing import Self, Any
from abc import ABC, abstractmethod

import beet

from rhombus.core.utils import BeetFile, fields, FROM_CONTEXT, JSONValue, contextfunction
from rhombus import config

__all__ = ["RhombusASTNode"]
    
IGNORED = object()
"Typing sentinel to indicate that inputs on an argument will have no effect"

class RhombusASTNode(ABC):
    "Base class for all nodes in a Rhombus AST"
    
    def __init_subclass__(cls, **kwargs):   
        super().__init_subclass__(**kwargs)

        # if (sig := inspect.signature(getattr(cls, "serialize"))) is None:
        #     raise TypeError
        # else:
        #     if "inline" not in sig.parameters:
        #         raise TypeError("serialize must accept inline")
        # if (sig := inspect.signature(getattr(cls, "deserialize"))) is None:
        #     raise TypeError
        # else:
        #     if "inline" not in sig.parameters:
        #         raise TypeError("serialize must accept inline")
        #     if "dp" not in sig.parameters:
        #         raise TypeError("serialize must accept inline")

        
    #======// Standard Implementations //========================================================//
    
    @property
    def fields(self) -> dict[str, Any]:
        "Standard implemenation for getting all parameters of the Node paired with their values."
        return fields(self)
    
    def additional_described_files(self) -> dict[str, BeetFile]:
        "Standard implementation for recursive search for additional files. Returns all files of all entries in `~.fields`."
        # Additionaly and excluding the one with the content of ~.serialize()
        files = {}
        for param, value in self.fields.items():
            if isinstance(value, RhombusASTNode):
                files |= value.additional_described_files()
        return files
        
    #======// Typing //==========================================================================//
    
    @abstractmethod
    def serialize(self, inline: bool = True) -> JSONValue:
        """Creates a dictionary containing the data serialized into the target format (primarily JSON).

        Only top-level, unreferenced data is retained. Nodes that generate references
        only leave behind those references. To retrieve the data associated with the
        references, use `~.additional_described_files()`.
        
        Parameters:
            inline (bool): Whether the data to be serialized is to be found not at the top level of
                the target file or it is. This parameter was introduced to signal whether to use
                the raw data or a reference string when serializing DatapackResources, however the
                exact implementation and use is left to the Node subclass.
        """
        raise NotImplementedError
    
    @classmethod
    @contextfunction(dp=config.ctx.datapack)
    @abstractmethod
    def deserialize(cls, data: JSONValue | Any, inline: bool, dp: beet.DataPack | None = FROM_CONTEXT) -> Self:
        """Creates an instance of the class based on available data.
        
        Parameters:
            data: ...
            inline (bool): ...
            dp (DataPack | None): Beet datapack from which references are to be resolved
        """
        raise NotImplementedError