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

    meta_new = VersionedNode.__rhombus_fields__["new_field"]
    meta_old = VersionedNode.__rhombus_fields__["old_field"]
    meta_renamed = VersionedNode.__rhombus_fields__["renamed_field"]

    rho.set_version(minecraft="1.19")
    assert not meta_new.is_present(rho)
    assert meta_old.is_present(rho)
    assert meta_renamed.get_appropriate_key(rho, "renamed_field") == "renamed_field"

    rho.set_version(minecraft="1.17")
    assert meta_renamed.get_appropriate_key(rho, "renamed_field") == "old_name"

    rho.set_version(minecraft="1.20")
    assert meta_new.is_present(rho)
    assert not meta_old.is_present(rho)


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
