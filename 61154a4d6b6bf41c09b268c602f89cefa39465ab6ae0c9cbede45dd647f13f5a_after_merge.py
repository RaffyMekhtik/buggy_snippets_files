def hy_eval(hytree, namespace=None, module_name=None, ast_callback=None):
    """``eval`` evaluates a quoted expression and returns the value. The optional
    second and third arguments specify the dictionary of globals to use and the
    module name. The globals dictionary defaults to ``(local)`` and the module
    name defaults to the name of the current module.

       => (eval '(print "Hello World"))
       "Hello World"

    If you want to evaluate a string, use ``read-str`` to convert it to a
    form first:

       => (eval (read-str "(+ 1 1)"))
       2"""
    if namespace is None:
        frame = inspect.stack()[1][0]
        namespace = inspect.getargvalues(frame).locals
    if module_name is None:
        m = inspect.getmodule(inspect.stack()[1][0])
        module_name = '__eval__' if m is None else m.__name__

    foo = HyObject()
    foo.start_line = 0
    foo.end_line = 0
    foo.start_column = 0
    foo.end_column = 0
    replace_hy_obj(hytree, foo)

    if not isinstance(module_name, string_types):
        raise HyTypeError(foo, "Module name must be a string")

    _ast, expr = hy_compile(hytree, module_name, get_expr=True)

    # Spoof the positions in the generated ast...
    for node in ast.walk(_ast):
        node.lineno = 1
        node.col_offset = 1

    for node in ast.walk(expr):
        node.lineno = 1
        node.col_offset = 1

    if ast_callback:
        ast_callback(_ast, expr)

    if not isinstance(namespace, dict):
        raise HyTypeError(foo, "Globals must be a dictionary")

    # Two-step eval: eval() the body of the exec call
    eval(ast_compile(_ast, "<eval_body>", "exec"), namespace)

    # Then eval the expression context and return that
    return eval(ast_compile(expr, "<eval>", "eval"), namespace)