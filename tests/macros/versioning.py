import pytest
from rhombus import rho
from rhombus.core.density_function import constant
from rhombus.std.macros import macro, implementation, resolve_ast_versioning

def test_macro_versioning_immediate():
    @macro
    def dummy() -> int:
        @implementation(until="1.18")
        def _():
            return 1
            
        @implementation(since="1.18", until="1.20")
        def _():
            return 2
            
        @implementation(since="1.20")
        def _():
            return 3
        
    rho.datapack_version = "1.17"
    assert dummy() == 1
    
    rho.datapack_version = "1.18"
    assert dummy() == 2
    
    rho.datapack_version = "1.19"
    assert dummy() == 2
    
    rho.datapack_version = "1.20"
    assert dummy() == 3
    
    rho.datapack_version = "1.21"
    assert dummy() == 3

def test_macro_versioning_lazy():
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
        
    rho.datapack_version = "1.17"
    assert resolve_ast_versioning(dummy().AST).value == 1.0
    
    rho.datapack_version = "1.18"
    assert resolve_ast_versioning(dummy().AST).value == 2.0
    
    rho.datapack_version = "1.19"
    assert resolve_ast_versioning(dummy().AST).value == 2.0
    
    rho.datapack_version = "1.20"
    assert resolve_ast_versioning(dummy().AST).value == 3.0
    
    rho.datapack_version = "1.21"
    assert resolve_ast_versioning(dummy().AST).value == 3.0

def test_macro_versioning_exceptions():
    @macro
    def dummy_since() -> int:
        @implementation(since="1.20")
        def _():
            return 1
        
    rho.datapack_version = "1.19"
    with pytest.raises(NotImplementedError):
        dummy_since()
        
    rho.datapack_version = "1.20"
    assert dummy_since() == 1
    
    @macro
    def dummy_missing_namespace() -> int:
        @implementation(since=("unknown_mod", "1.20"))
        def _():
            return 1
        
    with pytest.raises(NotImplementedError):
        dummy_missing_namespace()

def test_macro_versioning_default():
    @macro
    def dummy() -> int:
        @implementation(until="1.18")
        def _():
            return 1
            
        @implementation()
        def _():
            return 2
        
    rho.datapack_version = "1.17"
    assert dummy() == 1
    
    rho.datapack_version = "1.20"
    assert dummy() == 2
