    def _get_unitary_matrix(self, unitary):
        """Return the matrix representing a unitary operation.

        Args:
            unitary (~.Operation): a PennyLane unitary operation

        Returns:
            tf.Tensor[complex] or array[complex]: Returns a 2D matrix representation of
            the unitary in the computational basis, or, in the case of a diagonal unitary,
            a 1D array representing the matrix diagonal. For non-parametric unitaries,
            the return type will be a ``np.ndarray``. For parametric unitaries, a ``tf.Tensor``
            object will be returned.
        """
        op_name = unitary.name.split(".inv")[0]

        if op_name in self.parametric_ops:
            if op_name == "MultiRZ":
                mat = self.parametric_ops[op_name](*unitary.parameters, len(unitary.wires))
            else:
                mat = self.parametric_ops[op_name](*unitary.parameters)

            if unitary.inverse:
                mat = self._transpose(self._conj(mat))

            return mat

        if isinstance(unitary, DiagonalOperation):
            return unitary.eigvals

        return unitary.matrix