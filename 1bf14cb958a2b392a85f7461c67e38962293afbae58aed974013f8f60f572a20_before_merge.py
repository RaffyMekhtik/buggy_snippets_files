def radius_neighbors_graph(X, radius, mode='connectivity', metric='minkowski',
                           p=2, metric_params=None, include_self=False,
                           n_jobs=None):
    """Computes the (weighted) graph of Neighbors for points in X

    Neighborhoods are restricted the points at a distance lower than
    radius.

    Read more in the :ref:`User Guide <unsupervised_neighbors>`.

    Parameters
    ----------
    X : array-like or BallTree, shape = [n_samples, n_features]
        Sample data, in the form of a numpy array or a precomputed
        :class:`BallTree`.

    radius : float
        Radius of neighborhoods.

    mode : {'connectivity', 'distance'}, optional
        Type of returned matrix: 'connectivity' will return the connectivity
        matrix with ones and zeros, and 'distance' will return the distances
        between neighbors according to the given metric.

    metric : string, default 'minkowski'
        The distance metric used to calculate the neighbors within a
        given radius for each sample point. The DistanceMetric class
        gives a list of available metrics. The default distance is
        'euclidean' ('minkowski' metric with the param equal to 2.)

    p : int, default 2
        Power parameter for the Minkowski metric. When p = 1, this is
        equivalent to using manhattan_distance (l1), and euclidean_distance
        (l2) for p = 2. For arbitrary p, minkowski_distance (l_p) is used.

    metric_params : dict, optional
        additional keyword arguments for the metric function.

    include_self : bool, default=False
        Whether or not to mark each sample as the first nearest neighbor to
        itself. If `None`, then True is used for mode='connectivity' and False
        for mode='distance' as this will preserve backwards compatibility.

    n_jobs : int, optional (default = 1)
        The number of parallel jobs to run for neighbors search.
        If ``-1``, then the number of jobs is set to the number of CPU cores.

    Returns
    -------
    A : sparse matrix in CSR format, shape = [n_samples, n_samples]
        A[i, j] is assigned the weight of edge that connects i to j.

    Examples
    --------
    >>> X = [[0], [3], [1]]
    >>> from sklearn.neighbors import radius_neighbors_graph
    >>> A = radius_neighbors_graph(X, 1.5, mode='connectivity',
    ...                            include_self=True)
    >>> A.toarray()
    array([[1., 0., 1.],
           [0., 1., 0.],
           [1., 0., 1.]])

    See also
    --------
    kneighbors_graph
    """
    if not isinstance(X, RadiusNeighborsMixin):
        X = NearestNeighbors(radius=radius, metric=metric, p=p,
                             metric_params=metric_params, n_jobs=n_jobs).fit(X)
    else:
        _check_params(X, metric, p, metric_params)

    query = _query_include_self(X, include_self)
    return X.radius_neighbors_graph(query, radius, mode)