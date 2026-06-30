from rhombus.core.serializer import serialize_any_inline, deserialize_any_inline
from rhombus.core.node import RhombusASTNode

class DummyNode(RhombusASTNode):
    val: int
    
    def serialize_inline(self):
        return {"dummy": self.val}
        
    @classmethod
    def deserialize_inline(cls, data):
        return cls(val=data["dummy"])

def test_serialize_basic_types():
    assert serialize_any_inline(5) == 5
    assert serialize_any_inline("test") == "test"
    assert serialize_any_inline({"a": 1, "b": [2, 3]}) == {"a": 1, "b": [2, 3]}

def test_serialize_node():
    node = DummyNode(val=42)
    assert serialize_any_inline(node) == {"dummy": 42}
    
def test_deserialize_basic_types():
    assert deserialize_any_inline(5, int) == 5
    assert deserialize_any_inline("test", str) == "test"
    assert deserialize_any_inline(True, bool) == True
    
def test_deserialize_node():
    node = deserialize_any_inline({"dummy": 42}, DummyNode)
    assert isinstance(node, DummyNode)
    assert node.val == 42
