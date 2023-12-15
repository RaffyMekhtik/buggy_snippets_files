def rechunk(a, chunk_size, threshold=None, chunk_size_limit=None):
    if isinstance(a, DATAFRAME_TYPE):
        itemsize = max(dt.itemsize for dt in a.dtypes)
    else:
        itemsize = a.dtype.itemsize
    chunk_size = get_nsplits(a, chunk_size, itemsize)
    if chunk_size == a.nsplits:
        return a

    op = DataFrameRechunk(chunk_size, threshold, chunk_size_limit)
    return op(a)