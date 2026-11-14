from rhombus.core.models import DatapackNode, serialize_any_inline, deserialize_any_inline


class DummyNode(DatapackNode):
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


def test_deserialize_forward_ref_and_custom_node():
    from rhombus.core import DatapackResource, DensityFunction

    class CustomConfig(DatapackResource):
        scale: float = 1.0

    class CustomDensity(DensityFunction):
        id = "test:custom_density"
        config: "CustomConfig"

    # Forward reference as string without hardcoded knowledge
    node = deserialize_any_inline("minecraft:custom_ref", "CustomConfig")
    assert isinstance(node, CustomConfig)
    assert node.identifier == "minecraft:custom_ref"

    # Deserializing via DensityFunction
    from rhombus.runtime import rho
    rho.density_function_type_deserialization_register["test:custom_density"] = CustomDensity

    df = DensityFunction.deserialize_toplevel(
        {"type": "test:custom_density", "config": "minecraft:custom_ref"}
    )
    assert isinstance(df, CustomDensity)
    assert isinstance(df.config, CustomConfig)
    assert df.config.identifier == "minecraft:custom_ref"
