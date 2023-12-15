    def run_pass(self, state):
        """
        This prunes dead branches, a dead branch is one which is derivable as
        not taken at compile time purely based on const/literal evaluation.
        """
        assert state.func_ir
        msg = ('Internal error in pre-inference dead branch pruning '
               'pass encountered during compilation of '
               'function "%s"' % (state.func_id.func_name,))
        with fallback_context(state, msg):
            rewrite_semantic_constants(state.func_ir, state.args)

        if config.DEBUG or config.DUMP_IR:
            print('branch_pruned_ir'.center(80, '-'))
            print(state.func_ir.dump())
            print('end branch_pruned_ir'.center(80, '-'))
        return True