from typing import ClassVar
import pytest
import dataclasses

from rhombus.core.models import DatapackNode, field
from rhombus import rho


def test_fields():
    class DummyNode(DatapackNode):
        a: int
        b: str = "test"

    node = DummyNode(a=5)

    assert node.a == 5
    assert node.b == "test"

    with pytest.raises(dataclasses.FrozenInstanceError):
        node.a = 10


def test_equality():
    class DummyNode(DatapackNode):
        a: int

    node1 = DummyNode(a=5)
    node2 = DummyNode(a=5)
    node3 = DummyNode(a=6)

    assert node1 == node2
    assert node1 != node3


def test_versioning():
    class VersionedNode(DatapackNode):
        id: ClassVar[str] = field("my_id", legacy_values={"1.19": "my_legacy_id"})
        new_field: str | None = field(default=None, added_with="1.20")
        old_field: str | None = field(default=None, removed_with="1.19.4")
        renamed_field: str | None = field(default=None, legacy_keys={"1.18": "old_name"})
        typed_field: int | str = field(default="test", legacy_types={"1.18": int})

    meta_new = VersionedNode.__rhombus_fields__["new_field"]
    meta_old = VersionedNode.__rhombus_fields__["old_field"]
    meta_renamed = VersionedNode.__rhombus_fields__["renamed_field"]
    meta_typed = VersionedNode.__rhombus_fields__["typed_field"]

    rho.set_version(minecraft="1.19")
    assert not meta_new.is_present(rho)
    assert meta_old.is_present(rho)
    assert meta_renamed.get_appropriate_key(rho, "renamed_field") == "renamed_field"
    assert meta_typed.get_appropriate_type(rho, int | str) == int | str

    rho.set_version(minecraft="1.17")
    assert meta_renamed.get_appropriate_key(rho, "renamed_field") == "old_name"
    assert meta_typed.get_appropriate_type(rho, int | str) is int

    rho.set_version(minecraft="1.20")
    assert meta_new.is_present(rho)
    assert not meta_old.is_present(rho)
    assert meta_typed.get_appropriate_type(rho, int | str) == int | str


def test_validation():
    class ValidatedNode(DatapackNode):
        count: int = field(default=1, validate=lambda x: x > 0)
        complex: int = field(default=5, validate=lambda x, node: x == node.other_field)
        other_field: int = 5

    with pytest.warns(UserWarning, match="Validation failed for field 'count'"):
        ValidatedNode(count=-1, complex=5, other_field=5)

    with pytest.warns(UserWarning, match="Validation failed for field 'complex'"):
        ValidatedNode(count=1, complex=4, other_field=5)

    # Should not emit warnings
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ValidatedNode(count=1, complex=5, other_field=5)

    class TypedVersionNode(DatapackNode):
        coord: int | str = field(default=0, legacy_types={"1.18": int})

    rho.set_version(minecraft="1.17")
    with pytest.warns(UserWarning, match="Type mismatch in 'TypedVersionNode.coord'"):
        TypedVersionNode(coord="legacy_string")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        TypedVersionNode(coord=42)

    rho.set_version(minecraft="1.20")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        TypedVersionNode(coord="modern_string")
        TypedVersionNode(coord=42)


def test_defer_parametrization():
    from rhombus.core.abstract import RhombusASTNode

    def typed_func() -> int:
        return 42

    node = RhombusASTNode.defer(typed_func)
    assert node.return_type is int
    assert getattr(node, "__orig_class__", None) == RhombusASTNode[int]
    assert node.build() == 42

    def untyped_func():
        return "hello"

    untyped_node = RhombusASTNode.defer(untyped_func)
    assert untyped_node.build() == "hello"
