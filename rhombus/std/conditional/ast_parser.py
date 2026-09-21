import ast
import inspect
import textwrap
from typing import Callable, Any




def _dsl_if_helper(cond: Any, true_func: Callable[[], Any], false_func: Callable[[], Any]) -> Any:
    # Resolve condition class dynamically to avoid circular imports
    from rhombus.std.conditional.fluent import Condition, Causality
    if isinstance(cond, Condition):
        # We know it returns a Causality if we call .then()
        return cond.then(true_func()).otherwise(false_func())
    elif isinstance(cond, Causality):
        raise TypeError("Causality cannot be used as a condition")
    else:
        return true_func() if cond else false_func()

def _dsl_if_block_helper(cond: Any, true_fn: Callable[..., Any], false_fn: Callable[..., Any], *args):
    from rhombus.std.conditional.fluent import Condition, Causality
    if isinstance(cond, Condition):
        t_vals, t_has_ret, t_ret = true_fn(*args)
        f_vals, f_has_ret, f_ret = false_fn(*args)
        
        merged_vars = []
        for t, f in zip(t_vals, f_vals):
            if t is f:
                merged_vars.append(t)
            else:
                merged_vars.append(cond.then(t).otherwise(f))
        merged_vars = tuple(merged_vars)
        
        if t_has_ret and f_has_ret:
            return merged_vars, True, cond.then(t_ret).otherwise(f_ret)
        elif t_has_ret or f_has_ret:
            raise TypeError("In DSL mode, if one branch of an if-statement returns, the other branch must also return.")
        else:
            return merged_vars, False, None
    elif isinstance(cond, Causality):
        raise TypeError("Causality cannot be used as a condition")
    else:
        if cond:
            vals, has_ret, ret = true_fn(*args)
        else:
            vals, has_ret, ret = false_fn(*args)
        return vals, has_ret, ret

class ConditionalTransformer(ast.NodeTransformer):
    def __init__(self):
        self.counter = 0

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

    def visit_If(self, node: ast.If):
        self.generic_visit(node)
        
        class AssignFinder(ast.NodeVisitor):
            def __init__(self):
                self.names = set()
                self.has_return = False
            def visit_Name(self, n):
                if isinstance(n.ctx, ast.Store) and not n.id.startswith('_dsl_'):
                    self.names.add(n.id)
            def visit_Return(self, n):
                self.has_return = True
            def visit_FunctionDef(self, n): pass
            def visit_ClassDef(self, n): pass
            
        finder = AssignFinder()
        for stmt in node.body + node.orelse:
            finder.visit(stmt)
            
        assigned_names = sorted(list(finder.names))
        
        if not assigned_names and not finder.has_return:
            return node
            
        self.counter += 1
        fn_true_name = f"_true_fn_{self.counter}"
        fn_false_name = f"_false_fn_{self.counter}"
        
        class ReturnRewriter(ast.NodeTransformer):
            def visit_Return(self, n: ast.Return):
                ret_val = n.value if n.value else ast.Constant(value=None)
                return ast.Return(
                    value=ast.Tuple(
                        elts=[
                            ast.Tuple(elts=[ast.Name(id=name, ctx=ast.Load()) for name in assigned_names], ctx=ast.Load()),
                            ast.Constant(value=True),
                            ret_val
                        ],
                        ctx=ast.Load()
                    )
                )
            def visit_FunctionDef(self, n): return n
            def visit_ClassDef(self, n): return n
            
        def make_inner_func(name, statements):
            args = ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg=f"_{n}") for n in assigned_names],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]
            )
            
            init_assigns = [
                ast.Assign(
                    targets=[ast.Name(id=n, ctx=ast.Store())],
                    value=ast.Name(id=f"_{n}", ctx=ast.Load())
                ) for n in assigned_names
            ]
            
            rewriter = ReturnRewriter()
            rewritten_stmts = [rewriter.visit(s) for s in statements]
            
            ret_stmt = ast.Return(
                value=ast.Tuple(
                    elts=[
                        ast.Tuple(elts=[ast.Name(id=n, ctx=ast.Load()) for n in assigned_names], ctx=ast.Load()),
                        ast.Constant(value=False),
                        ast.Constant(value=None)
                    ],
                    ctx=ast.Load()
                )
            )
            
            return ast.FunctionDef(
                name=name,
                args=args,
                body=init_assigns + rewritten_stmts + [ret_stmt],
                decorator_list=[],
                returns=None
            )
            
        true_fn = make_inner_func(fn_true_name, node.body)
        false_fn = make_inner_func(fn_false_name, node.orelse)
        
        call_args = [
            node.test,
            ast.Name(id=fn_true_name, ctx=ast.Load()),
            ast.Name(id=fn_false_name, ctx=ast.Load())
        ]
        for n in assigned_names:
            get_call = ast.Call(
                func=ast.Attribute(
                    value=ast.Call(func=ast.Name(id='locals', ctx=ast.Load()), args=[], keywords=[]),
                    attr='get',
                    ctx=ast.Load()
                ),
                args=[ast.Constant(value=n)],
                keywords=[]
            )
            call_args.append(get_call)
            
        helper_call = ast.Call(
            func=ast.Name(id='_dsl_if_block_helper', ctx=ast.Load()),
            args=call_args,
            keywords=[]
        )
        
        assign_helper = ast.Assign(
            targets=[ast.Tuple(elts=[
                ast.Name(id='_dsl_vars', ctx=ast.Store()),
                ast.Name(id='_dsl_has_ret', ctx=ast.Store()),
                ast.Name(id='_dsl_ret', ctx=ast.Store())
            ], ctx=ast.Store())],
            value=helper_call
        )
        
        nodes_to_return = [true_fn, false_fn, assign_helper]
        
        if assigned_names:
            assign_vars = ast.Assign(
                targets=[ast.Tuple(elts=[ast.Name(id=n, ctx=ast.Store()) for n in assigned_names], ctx=ast.Store())],
                value=ast.Name(id='_dsl_vars', ctx=ast.Load())
            )
            nodes_to_return.append(assign_vars)
            
        if_ret = ast.If(
            test=ast.Name(id='_dsl_has_ret', ctx=ast.Load()),
            body=[ast.Return(value=ast.Name(id='_dsl_ret', ctx=ast.Load()))],
            orelse=[]
        )
        nodes_to_return.append(if_ret)
        
        return nodes_to_return

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

    transformer = ConditionalTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    func_globals = func.__globals__.copy()
    func_globals['_dsl_if_helper'] = _dsl_if_helper
    func_globals['_dsl_if_block_helper'] = _dsl_if_block_helper

    code = compile(new_tree, filename=func.__code__.co_filename, mode='exec')
    local_ns = {}
    exec(code, func_globals, local_ns)
    
    if func.__name__ in local_ns:
        return local_ns[func.__name__]
    return func

