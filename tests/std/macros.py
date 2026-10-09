import pytest
from rhombus import rho
from rhombus.core.models import constant
from rhombus.std.macros import macro, implementation


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
    assert dummy().AST.build().value == 1.0
    
    rho.set_version(minecraft="1.18")
    assert dummy().AST.build().value == 2.0
    
    rho.set_version(minecraft="1.19")
    assert dummy().AST.build().value == 2.0
    
    rho.set_version(minecraft="1.20")
    assert dummy().AST.build().value == 3.0
    
    rho.set_version(minecraft="1.21")
    assert dummy().AST.build().value == 3.0


def test_no_implementations():
    @macro
    def dummy_since() -> int:
        @implementation(since="1.20")
        def _():
            return 1
        
    rho.set_version(minecraft="1.19")
    with pytest.raises(NotImplementedError):
        dummy_since().AST.build()
        
    rho.set_version(minecraft="1.20")
    assert dummy_since().AST.build().value == 1.0
    
    @macro
    def dummy_missing_namespace() -> int:
        @implementation(since=("unknown_mod", "1.20"))
        def _():
            return 1
        
    with pytest.raises(NotImplementedError):
        dummy_missing_namespace().AST.build()


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
    assert dummy().AST.build().value == 1.0
    
    rho.set_version(minecraft="1.20")
    assert dummy().AST.build().value == 2.0
