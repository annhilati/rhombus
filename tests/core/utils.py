from rhombus.core import utils


def test_uuid_hash():
    data1 = {"a": 1, "b": 2}
    data2 = {"b": 2, "a": 1}
    assert utils.JSON_hash(data1) == utils.JSON_hash(data2)
    assert len(utils.JSON_hash(data1)) == 32