def grid_to_graph(n_x, n_y, n_z=1, mask=None, return_as=sparse.coo_matrix,
                  dtype=np.int):
    """Graph of the pixel-to-pixel connections

    Edges exist if 2 voxels are connected.

    Parameters
    ===========
    n_x: int
        Dimension in x axis
    n_y: int
        Dimension in y axis
    n_z: int, optional, default 1
        Dimension in z axis
    mask : ndarray of booleans, optional
        An optional mask of the image, to consider only part of the
        pixels.
    return_as: np.ndarray or a sparse matrix class, optional
        The class to use to build the returned adjacency matrix.
    dtype: dtype, optional, default int
        The data of the returned sparse matrix. By default it is int

    Notes
    ===========
    For sklearn versions 0.14.1 and prior, return_as=np.ndarray was handled
    by returning a dense np.matrix instance.  Going forward, np.ndarray
    returns an np.ndarray, as expected.

    For compatibility, user code relying on this method should wrap its
    calls in ``np.asarray`` to avoid type issues.
    """
    return _to_graph(n_x, n_y, n_z, mask=mask, return_as=return_as,
                     dtype=dtype)