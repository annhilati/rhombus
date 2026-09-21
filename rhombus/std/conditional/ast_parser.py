import ast
import inspect
import textwrap
from typing import Callable, Any

from rhombus.std.conditional.fluent import Condition, Causality


def _dsl_if_helper(cond: Any, true_func: Callable[[], Any], false_func: Callable[[], Any]) -> Any:
    # Resolve condition class dynamically to avoid circular imports
    if isinstance(cond, Condition):
        # We know it returns a Causality if we call .then()
        return cond.then(true_func()).otherwise(false_func())
    elif isinstance(cond, Causality):
        # In case someone does (when(a).equals(b).then(c)) in a ternary... wait, causality can't be condition.
        raise TypeError("Causality cannot be used as a condition")
    else:
        return true_func() if cond else false_func()

class InlineIfTransformer(ast.NodeTransformer):
    def visit_IfExp(self, node: ast.IfExp) -> Any:
        self.generic_visit(node)
        
        true_lambda = ast.Lambda(
            args=ast.arguments(posonlyargs=[], args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
            body=node.body
        )
        false_lambda = ast.Lambda(
            args=ast.arguments(posonlyargs=[], args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
            body=node.orelse
        )
        
        func_name = ast.Name(id='_dsl_if_helper', ctx=ast.Load())
        call_node = ast.Call(func=func_name, args=[node.test, true_lambda, false_lambda], keywords=[])
        return ast.copy_location(call_node, node)

def transform_ast(func: Callable) -> Callable:
    try:
        source = inspect.getsource(func)
    except (TypeError, OSError):
        return func
        
    source = textwrap.dedent(source)
    
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return func

    transformer = InlineIfTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    func_globals = func.__globals__.copy()
    func_globals['_dsl_if_helper'] = _dsl_if_helper

    code = compile(new_tree, filename=func.__code__.co_filename, mode='exec')
    local_ns = {}
    exec(code, func_globals, local_ns)
    
    if func.__name__ in local_ns:
        return local_ns[func.__name__]
    return func
