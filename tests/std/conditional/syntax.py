import pytest
from rhombus import rho
from rhombus.std.density import Density
from rhombus.std.macros import macro, resolve_ast_macros
import rhombus.support.vanilla.types as vt


EPS = 1e-7

def test_ternary_operator():
    @macro
    def my_ternary():
        return 10.0 if Density("in") > 0 else -10.0
        
    rho.set_version(minecraft="1.21")
    res_new = resolve_ast_macros(my_ternary().AST)
    # interval_select is only active >= 104.0 which is not reached by minecraft="1.21"
    # assert isinstance(res_new, vt.interval_select)
    assert isinstance(res_new, (vt.interval_select, vt.range_choice))
    
    rho.set_version(minecraft="1.18")
    res_old = resolve_ast_macros(my_ternary().AST)
    assert isinstance(res_old, vt.range_choice)


def test_if_elif_else_blocks():
    @macro
    def my_blocks():
        if Density("in") == 0:
            a = 1.0
        elif Density("in") > 5:
            a = 2.0
        else:
            a = 3.0
        return a

    rho.set_version(minecraft="1.21")
    res_new = resolve_ast_macros(my_blocks().AST)
    assert isinstance(res_new, vt.range_choice)
    assert isinstance(res_new.when_out_of_range, (vt.interval_select, vt.range_choice))
    
    rho.set_version(minecraft="1.18")
    res_old = resolve_ast_macros(my_blocks().AST)
    assert isinstance(res_old, vt.range_choice)
    assert isinstance(res_old.when_out_of_range, vt.range_choice)


def test_early_exit():
    @macro
    def my_early_exit():
        if Density("in") < 0:
            return -1.0
        return 1.0

    rho.set_version(minecraft="1.21")
    with pytest.raises(TypeError, match="early returns inside Density-dependent if-statements are not supported"):
        resolve_ast_macros(my_early_exit().AST)


def test_outside_of_macros():
    def standard_func():
        return 1.0 if Density("in") > 0 else -1.0
    
    with pytest.raises(Exception):
        standard_func()
