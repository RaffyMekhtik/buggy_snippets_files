        def op_CALL_FUNCTION_KW(self, inst, func, args, names, res):
            func = self.get(func)
            args = [self.get(x) for x in args]
            # Find names const
            names = self.get(names)
            for inst in self.current_block.body:
                if isinstance(inst, ir.Assign) and inst.target is names:
                    self.current_block.remove(inst)
                    keys = inst.value.value
                    break

            nkeys = len(keys)
            posvals = args[:-nkeys]
            kwvals = args[-nkeys:]
            keyvalues = list(zip(keys, kwvals))

            expr = ir.Expr.call(func, posvals, keyvalues, loc=self.loc)
            self.store(expr, res)