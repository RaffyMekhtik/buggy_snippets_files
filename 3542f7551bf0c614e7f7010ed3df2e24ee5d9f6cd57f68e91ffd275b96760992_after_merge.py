    def runsource(self, source, filename='<input>', symbol='single'):
        global SIMPLE_TRACEBACKS
        try:
            try:
                do = import_buffer_to_hst(source)
            except PrematureEndOfInput:
                return True
        except LexException as e:
            if e.source is None:
                e.source = source
                e.filename = filename
            print(e, file=sys.stderr)
            return False

        try:
            def ast_callback(main_ast, expr_ast):
                if self.spy:
                    # Mush the two AST chunks into a single module for
                    # conversion into Python.
                    new_ast = ast.Module(main_ast.body +
                                         [ast.Expr(expr_ast.body)])
                    print(astor.to_source(new_ast))
            value = hy_eval(do, self.locals, "__console__",
                            ast_callback)
        except HyTypeError as e:
            if e.source is None:
                e.source = source
                e.filename = filename
            if SIMPLE_TRACEBACKS:
                print(e, file=sys.stderr)
            else:
                self.showtraceback()
            return False
        except Exception:
            self.showtraceback()
            return False

        if value is not None:
            # Make the last non-None value available to
            # the user as `_`.
            self.locals['_'] = value
            # Print the value.
            try:
                output = self.output_fn(value)
            except Exception:
                self.showtraceback()
                return False
            print(output)
        return False