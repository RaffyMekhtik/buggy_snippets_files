def dask_rolling_wrapper(moving_func, a, window, min_count=None, axis=-1):
    '''wrapper to apply bottleneck moving window funcs on dask arrays'''
    dtype, fill_value = dtypes.maybe_promote(a.dtype)
    a = a.astype(dtype)
    # inputs for ghost
    if axis < 0:
        axis = a.ndim + axis
    depth = {d: 0 for d in range(a.ndim)}
    depth[axis] = window - 1
    boundary = {d: fill_value for d in range(a.ndim)}
    # create ghosted arrays
    ag = da.ghost.ghost(a, depth=depth, boundary=boundary)
    # apply rolling func
    out = ag.map_blocks(moving_func, window, min_count=min_count,
                        axis=axis, dtype=a.dtype)
    # trim array
    result = da.ghost.trim_internal(out, depth)
    return result