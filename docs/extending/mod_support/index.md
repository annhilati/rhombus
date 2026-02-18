---
title: Overview
icon: lucide/package-open
---

# Adding Support for Content from Mods

!!! tip
    Rhombus already has functions and classes for relevant mods built-in. They are located in modules in `Rhombus.support`.
    If you need support for a mod that is currently not present in the `support` collection, you can file an [issue](https://github.com/annhilati/rhombus/issues) or contribute.

To add support for mods, you can use the infrastructure on which the built-ins are also based. There are base classes for various scenarios.

<div class="grid cards" markdown>

-   **Density Function Type**

    ---
    A type of operator at the Java level that is used to perform density calculations.

    :octicons-arrow-right-24: [Class inheriting from `DensityFunction`](density_functions.md)<br>
    :octicons-arrow-right-24: [Builtin macro producing an corresponding `Density`]

-   **Datapack Resource**

    ---
    A resource that comes with an datapack and can be referenced in a field of a density function type.

    :octicons-arrow-right-24: [Class inheriting from `RegistryResource`](datapack_resources.md)<br>

</div>