from rhombus.core.datapack_resource import DatapackResource
import beet


class DummyResource(DatapackResource):
    fileclass = beet.JsonFile
    val: int


def test_referencing():
    res = DummyResource.refer("my:reference")
    assert res.is_reference
    assert res.identifier == "my:reference"


def test_naming():
    res = "my:reference" @ DummyResource(5)
    assert not res.is_reference
    assert res.identifier == "my:reference"
    assert res.val == 5


def test_serialization():
    res = DummyResource(val=42)
    assert not res.is_reference
    assert res.serialize_toplevel() == {"val": 42}


def test_deserialization():
    res = DummyResource.from_dict({"val": 42})
    assert isinstance(res, DummyResource)
    assert res.val == 42
    assert not res.is_reference
