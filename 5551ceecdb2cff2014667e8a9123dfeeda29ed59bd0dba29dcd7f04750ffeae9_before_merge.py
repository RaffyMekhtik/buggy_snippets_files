    def unify_types(self, *typelist):
        # Sort the type list according to bit width before doing
        # pairwise unification (with thanks to aterrel).
        def keyfunc(obj):
            """Uses bitwidth to order numeric-types.
            Fallback to hash() for arbitary ordering.
            """
            return getattr(obj, 'bitwidth', hash(obj))

        typelist = sorted(typelist, key=keyfunc)
        unified = typelist[0]
        for tp in typelist[1:]:
            unified = self.unify_pairs(unified, tp)
            if unified is None:
                break
        return unified