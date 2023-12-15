    def __init__(self, dtype=None, to_fetch_keys=None, to_fetch_idxes=None, **kw):
        kw.pop('output_types', None)
        kw.pop('_output_types', None)
        super().__init__(
            _dtype=dtype, _to_fetch_keys=to_fetch_keys, _to_fetch_idxes=to_fetch_idxes, **kw)