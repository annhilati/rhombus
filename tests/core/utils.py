from rhombus.core import utils
import dataclasses

def test_uuid_hash():
    data1 = {"a": 1, "b": 2}
    data2 = {"b": 2, "a": 1}
    assert utils.uuid_hash(data1) == utils.uuid_hash(data2)
    assert len(utils.uuid_hash(data1)) == 32

def test_fields():
    @dataclasses.dataclass
    class Dummy:
        a: int
        b: str = "default"
        c: float = dataclasses.field(init=False, default=1.0)
        
    d = Dummy(a=5)
    flds = utils.fields(d)
    assert flds == {"a": 5, "b": "default"}
    assert "c" not in flds

def test_annotated_fields():
    @dataclasses.dataclass
    class Dummy:
        a: int
        b: str = "default"
        c: float = dataclasses.field(init=False, default=1.0)
        
    flds = utils.annotated_fields(Dummy)
    assert flds == {"a": int, "b": str}
    assert "c" not in flds
