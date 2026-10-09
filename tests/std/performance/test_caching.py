from rhombus import rho
from rhombus.std.coords import x
from rhombus.std.caching import new_cache_transformer
from rhombus.std.density import Density
import rhombus.support.vanilla.types as vt

def test_x_macro_size():
    rho.set_version(minecraft='1.21')
    
    info = x().info()
    
    # 305 nodes in 1.21
    assert info.toplevel_nodes == 305

def test_cache_conditions():
    rho.set_version(minecraft='1.21')
    
    # We create a dummy node that is small
    small_df = Density(1.0) + 2.0
    # size is 3: add(constant, constant)
    
    # We create a big node
    big_df = (Density(1.0) + 2.0) + (Density(3.0) + 4.0)
    # size is 7
    
    # Let's test occurrences. We reuse small_df 3 times.
    expr = small_df + (small_df + small_df)
    
    # new_cache_transformer with targets
    cached_expr = new_cache_transformer(expr, targets=[small_df], min_size=5, min_occurances=2)
    # small_df should NOT be cached because size 3 < 5, even though it's in targets!
    assert cached_expr.info().unique_cached_nodes == 0

    # new_cache_transformer without targets
    cached_expr2 = new_cache_transformer(expr, min_size=5, min_occurances=2)
    # small_df should NOT be cached because size is 3 < 5
    assert cached_expr2.info().unique_cached_nodes == 0
    
    # test size constraint passing without targets
    expr_big = big_df + (big_df + big_df)
    cached_expr3 = new_cache_transformer(expr_big, min_size=5, min_occurances=2)
    # big_df should be cached because size is 7 >= 5 and occurrences >= 2
    assert cached_expr3.info().unique_cached_nodes > 0
    
    # test size constraint passing with targets
    cached_expr4 = new_cache_transformer(expr_big, targets=[big_df], min_size=5, min_occurances=2)
    assert cached_expr4.info().unique_cached_nodes > 0

