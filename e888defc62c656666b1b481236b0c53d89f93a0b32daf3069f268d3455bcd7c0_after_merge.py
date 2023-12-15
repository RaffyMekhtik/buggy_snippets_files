    def apply(self):
        """
        Rewrite all matching getitems as static_getitems.
        """
        new_block = self.block.copy()
        new_block.clear()
        for inst in self.block.body:
            if isinstance(inst, ir.Assign):
                expr = inst.value
                if expr in self.getitems:
                    const = self.getitems[expr]
                    new_expr = ir.Expr.static_getitem(value=expr.value,
                                                      index=const,
                                                      index_var=expr.index,
                                                      loc=expr.loc)
                    inst = ir.Assign(value=new_expr, target=inst.target,
                                     loc=inst.loc)
            new_block.append(inst)
        return new_block