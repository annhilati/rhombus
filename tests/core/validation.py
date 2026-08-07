import pytest
from rhombus.core.node import RhombusASTNode, field

def test_validation_single_arg():
    class DummyNode(RhombusASTNode):
        val: int = field(validate=lambda x: x > 0)

    DummyNode(5)
    with pytest.raises(ValueError):
        DummyNode(-1)

def test_validation_double_arg():
    class DummyNode(RhombusASTNode):
        min_val: int
        max_val: int = field(validate=lambda v, self: v > self.min_val)

    DummyNode(min_val=10, max_val=20)
    with pytest.raises(ValueError):
        DummyNode(min_val=10, max_val=5)
