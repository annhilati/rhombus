from dataclasses import fields
from beet import DataPack
from beet.contrib.worldgen import WorldgenDensityFunction
from rhombus.language.density import Density
from rhombus.core.additional_resource import AdditionalResourceBase
from rhombus.core.df_types import DensityFunctionTypeBase, Reference

def compile(density: Density, datapack: DataPack, name: str) -> None:

    root = density.wrapped
    if ":" not in name: name = "minecraft:" + name
    namespace = name.split(":")[0]

    additional_resources: set[AdditionalResourceBase] = set()
    references: list[Reference] = []

    def search_for_additional_resources(o):
        print(type(o), o)
        if isinstance(o, DensityFunctionTypeBase):
            if isinstance(o, Reference):
                references.append(o)
            for value in [getattr(o, param) for param in {f.name for f in fields(o) if f.init}]:
                search_for_additional_resources(value)
        elif isinstance(o, (list, tuple)):
            for value in o:
                search_for_additional_resources(value)
        elif isinstance(o, AdditionalResourceBase):
            additional_resources.add(o)

    search_for_additional_resources(root)

    for resource in [ar for ar in additional_resources if ar.UUID is not None]:
        id = resource.reference_identifier
        cls = resource.fileclass
        datapack[id] = cls(resource.encode())

    for reference in [r for r in references if r.default is not None]:
        datapack[reference.id] = WorldgenDensityFunction(reference.default.encode())

    datapack[name] = WorldgenDensityFunction(root.encode())