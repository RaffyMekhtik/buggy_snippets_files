    def constrain_statement(self, inst):
        if isinstance(inst, ir.Assign):
            self.typeof_assign(inst)
        elif isinstance(inst, ir.SetItem):
            self.typeof_setitem(inst)
        elif isinstance(inst, ir.StaticSetItem):
            self.typeof_static_setitem(inst)
        elif isinstance(inst, ir.DelItem):
            self.typeof_delitem(inst)
        elif isinstance(inst, ir.SetAttr):
            self.typeof_setattr(inst)
        elif isinstance(inst, ir.Print):
            self.typeof_print(inst)
        elif isinstance(inst, ir.StoreMap):
            self.typeof_storemap(inst)
        elif isinstance(inst, (ir.Jump, ir.Branch, ir.Return, ir.Del)):
            pass
        elif isinstance(inst, (ir.StaticRaise, ir.StaticTryRaise)):
            pass
        elif type(inst) in typeinfer_extensions:
            # let external calls handle stmt if type matches
            f = typeinfer_extensions[type(inst)]
            f(inst, self)
        else:
            msg = "Unsupported constraint encountered: %s" % inst
            raise UnsupportedError(msg, loc=inst.loc)