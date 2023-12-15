    def get_tileable_nsplits(self, tileable, chunk_result=None):
        chunk_idx_to_shape = OrderedDict()
        tiled = get_tiled(tileable, mapping=tileable_optimized)
        chunk_result = chunk_result if chunk_result is not None else self._chunk_result
        for chunk in tiled.chunks:
            chunk_idx_to_shape[chunk.index] = chunk_result[chunk.key].shape
        return calc_nsplits(chunk_idx_to_shape)