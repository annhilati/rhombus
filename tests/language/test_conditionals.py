# from rhombus.language import Density, when, t

# def test_when_then_otherwise():

#     assert when(101, equals=5).then(1).otherwise(0) == Density(t.range_choice(input=t.constant(101.0), min_inclusive=5.0, max_exclusive=5.000001, when_in_range=t.constant(1.0), when_out_of_range=t.constant(0.0)))