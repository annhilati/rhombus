from beet import DataPack
from beet.contrib.worldgen import WorldgenDensityFunction
from rhombus.language.density import Density
from rhombus.core.additional_resource import AdditionalResourceBase
from rhombus.core.df_types import DensityFunctionTypeBase
from dataclasses import fields

def compile(density: Density, datapack: DataPack, name: str) -> None:

    root = density.wrapped

    additional_resources: set[AdditionalResourceBase] = set()

    def search_for_additional_resources(o):
        print(type(o), o)
        if isinstance(o, DensityFunctionTypeBase):
            for value in [getattr(o, param) for param in {f.name for f in fields(o) if f.init}]:
                search_for_additional_resources(value)
        elif isinstance(o, list):
            for value in o:
                search_for_additional_resources(value)
        elif isinstance(o, AdditionalResourceBase):
            additional_resources.add(o)

    search_for_additional_resources(root)

    for resource in additional_resources:
        id = resource.reference
        cls = resource.fileclass
        datapack[id] = cls(resource.encode())

    datapack[name] = WorldgenDensityFunction(root.encode())