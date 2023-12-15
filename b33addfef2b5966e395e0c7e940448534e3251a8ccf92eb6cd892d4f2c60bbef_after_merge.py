    def __call__(self, a):
        shape = tuple(s if np.isnan(s) else int(s)
                      for s in _reorder(a.shape, self._axes))
        if self._axes == list(reversed(range(a.ndim))):
            # order reversed
            tensor_order = reverse_order(a.order)
        else:
            tensor_order = TensorOrder.C_ORDER
        return self.new_tensor([a], shape, order=tensor_order)