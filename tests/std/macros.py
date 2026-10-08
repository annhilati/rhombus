import pytest
from rhombus import rho
from rhombus.core.density_function import constant
from rhombus.std.macros import macro, implementation, resolve_ast_macros


def test_version_selection():
    @macro
    def dummy():
        @implementation(until="1.18")
        def _():
            return constant(1.0)
            
        @implementation(since="1.18", until="1.20")
        def _():
            return constant(2.0)
            
        @implementation(since="1.20")
        def _():
            return constant(3.0)
        
    rho.set_version(minecraft="1.17")
    assert resolve_ast_macros(dummy().AST).value == 1.0
    
    rho.set_version(minecraft="1.18")
    assert resolve_ast_macros(dummy().AST).value == 2.0
    
    rho.set_version(minecraft="1.19")
    assert resolve_ast_macros(dummy().AST).value == 2.0
    
    rho.set_version(minecraft="1.20")
    assert resolve_ast_macros(dummy().AST).value == 3.0
    
    rho.set_version(minecraft="1.21")
    assert resolve_ast_macros(dummy().AST).value == 3.0


def test_no_implementations():
    @macro
    def dummy_since() -> int:
        @implementation(since="1.20")
        def _():
            return 1
        
    rho.set_version(minecraft="1.19")
    with pytest.raises(NotImplementedError):
        resolve_ast_macros(dummy_since().AST)
        
    rho.set_version(minecraft="1.20")
    assert resolve_ast_macros(dummy_since().AST).value == 1.0
    
    @macro
    def dummy_missing_namespace() -> int:
        @implementation(since=("unknown_mod", "1.20"))
        def _():
            return 1
        
    with pytest.raises(NotImplementedError):
        resolve_ast_macros(dummy_missing_namespace().AST)


def test_default_implementation():
    @macro
    def dummy() -> int:
        @implementation(until="1.18")
        def _():
            return 1
            
        @implementation()
        def _():
            return 2
        
    rho.set_version(minecraft="1.17")
    assert resolve_ast_macros(dummy().AST).value == 1.0
    
    rho.set_version(minecraft="1.20")
    assert resolve_ast_macros(dummy().AST).value == 2.0
