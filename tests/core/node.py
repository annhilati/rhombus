import pytest
import dataclasses
from rhombus.core.node import RhombusASTNode


def test_immutability():
    class DummyNode(RhombusASTNode):
        a: int
        b: str = "test"

    node = DummyNode(a=5)

    assert node.a == 5
    assert node.b == "test"

    with pytest.raises(dataclasses.FrozenInstanceError):
        node.a = 10


def test_fields():
    class DummyNode(RhombusASTNode):
        a: int
        b: str = "test"

    node = DummyNode(a=5)
    assert node.fields == {"a": 5, "b": "test"}


def test_equality():
    class DummyNode(RhombusASTNode):
        a: int

    node1 = DummyNode(a=5)
    node2 = DummyNode(a=5)
    node3 = DummyNode(a=6)

    assert node1 == node2
    assert node1 != node3
