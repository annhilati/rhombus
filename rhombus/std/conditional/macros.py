from __future__ import annotations
from rhombus.core.density_function import DensityFunction
from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro, implementation
import rhombus.support.vanilla.types as vt

OMEGA = vt.literal_number_limit

# IDEA: Move this
@macro
def range_choice(
    input: AnyDensity,
    min_inclusive: float,
    max_exclusive: float,
    when_in_range: AnyDensity,
    when_out_of_range: AnyDensity,
) -> Density:
    """Computes the input value, and depending on that result returns one of two other density functions.
    
    `range_choice` can be used like if-else-statements, but to build large conditionality trees use `~.when` instead.    
    ```
    if input >= min_inclucive:
        if input < max_exclusive:
            return when_in_range
    return when_out_of_range
    ```

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#range_choice)
    """
    @implementation()
    def _impl():
        return vt.range_choice(
            input.AST,
            min_inclusive,
            max_exclusive,
            when_in_range.AST,
            when_out_of_range.AST,
        )


@macro
def interval_select(
    input: AnyDensity, thresholds: list[float], functions: list[AnyDensity]
) -> Density:
    """Selects between a number of density functions based on an input density function and a set of threshold values.

    Parameters:
        input (density function): Density Function, to be compared with given thresholds.
        thresholds (list[float]):  Threshold values to compare input with. Must be non-empty.
            If `input < thresholds[i]`, `functions[i]` will be selected. If the input is greater than the last threshold value, the last function will be selected.
            Must be one fewer thresholds than functions.
        functions (list[density function]): List of density functions to be selected from. Must be one more element in functions than in thresholds.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#interval_select)
    """
    @implementation(until=104.0)
    def _legacy():
        result = functions[-1].AST
        for i in range(len(thresholds) - 1, -1, -1):
            result = vt.range_choice(input.AST, -OMEGA, thresholds[i], functions[i].AST, result)
        return result

    @implementation()
    def _impl():
        return vt.interval_select(
            input.AST, thresholds, [function.AST for function in functions]
        )
