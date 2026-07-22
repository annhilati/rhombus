from rhombus.core.datapack_resource import DatapackResource
import beet


class DummyResource(DatapackResource):
    fileclass = beet.JsonFile
    val: int


def test_resource_reference():
    res = DummyResource.refer("my:reference")
    assert res.is_reference
    assert res.identifier == "my:reference"


def test_resource_serialization():
    res = DummyResource(val=42)
    assert not res.is_reference
    assert res.serialize_toplevel() == {"val": 42}


def test_resource_from_dict():
    res = DummyResource.from_dict({"val": 42})
    assert isinstance(res, DummyResource)
    assert res.val == 42
    assert not res.is_reference
