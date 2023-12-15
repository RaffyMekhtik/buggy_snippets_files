    def get_data_type(self, ty):
        """
        Get a LLVM data representation of the Numba type *ty* that is safe
        for storage.  Record data are stored as byte array.

        The return value is a llvmlite.ir.Type object, or None if the type
        is an opaque pointer (???).
        """
        try:
            fac = type_registry.match(ty)
        except KeyError:
            pass
        else:
            return fac(self, ty)

        return self.data_model_manager[ty].get_data_type()