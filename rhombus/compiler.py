from dataclasses import fields
from beet import Context
from beet.contrib.worldgen import WorldgenDensityFunction
from rhombus.language.density import Density
from rhombus.core.additional_resource import AdditionalResourceBase
from rhombus.core.df_types import DensityFunctionTypeBase, Reference

def compile(ctx: Context, density: Density, identifier: str) -> None:
    data = ctx.data

    root = density.wrapped
    if ":" not in identifier: identifier = "minecraft:" + identifier

    additional_resources: set[AdditionalResourceBase] = set()
    references: list[Reference] = []

    def search_for_additional_resources(o):
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

    # Additional resources
    for resource in [ar for ar in additional_resources if ar.UUID is not None]:
        id = resource.reference_identifier
        cls = resource.fileclass
        data[id] = cls(resource.encode())
        print(f"Implemented {cls.__name__} '{id}'")

    # References with defaults
    for reference in [r for r in references if r.default is not None]:
        data[reference.reference] = WorldgenDensityFunction(reference.default.encode())
        print(f"Implemented density function '{reference.reference}' with its default value")

    data[identifier] = WorldgenDensityFunction(root.encode())
    print(f"Finished implementing density function '{identifier}'")