def dbscan(X, eps=0.5, min_samples=5, metric='minkowski',
           algorithm='auto', leaf_size=30, p=2, sample_weight=None,
           random_state=None):
    """Perform DBSCAN clustering from vector array or distance matrix.

    Parameters
    ----------
    X : array or sparse (CSR) matrix of shape (n_samples, n_features), or \
            array of shape (n_samples, n_samples)
        A feature array, or array of distances between samples if
        ``metric='precomputed'``.

    eps : float, optional
        The maximum distance between two samples for them to be considered
        as in the same neighborhood.

    min_samples : int, optional
        The number of samples (or total weight) in a neighborhood for a point
        to be considered as a core point. This includes the point itself.

    metric : string, or callable
        The metric to use when calculating distance between instances in a
        feature array. If metric is a string or callable, it must be one of
        the options allowed by metrics.pairwise.pairwise_distances for its
        metric parameter.
        If metric is "precomputed", X is assumed to be a distance matrix and
        must be square.

    algorithm : {'auto', 'ball_tree', 'kd_tree', 'brute'}, optional
        The algorithm to be used by the NearestNeighbors module
        to compute pointwise distances and find nearest neighbors.
        See NearestNeighbors module documentation for details.

    leaf_size : int, optional (default = 30)
        Leaf size passed to BallTree or cKDTree. This can affect the speed
        of the construction and query, as well as the memory required
        to store the tree. The optimal value depends
        on the nature of the problem.

    p : float, optional
        The power of the Minkowski metric to be used to calculate distance
        between points.

    sample_weight : array, shape (n_samples,), optional
        Weight of each sample, such that a sample with a weight of at least
        ``min_samples`` is by itself a core sample; a sample with negative
        weight may inhibit its eps-neighbor from being core.
        Note that weights are absolute, and default to 1.

    random_state: numpy.RandomState, optional
        Deprecated and ignored as of version 0.16, will be removed in version
        0.18. DBSCAN does not use random initialization.

    Returns
    -------
    core_samples : array [n_core_samples]
        Indices of core samples.

    labels : array [n_samples]
        Cluster labels for each point.  Noisy samples are given the label -1.

    Notes
    -----
    See examples/cluster/plot_dbscan.py for an example.

    This implementation bulk-computes all neighborhood queries, which increases
    the memory complexity to O(n.d) where d is the average number of neighbors,
    while original DBSCAN had memory complexity O(n).

    References
    ----------
    Ester, M., H. P. Kriegel, J. Sander, and X. Xu, "A Density-Based
    Algorithm for Discovering Clusters in Large Spatial Databases with Noise".
    In: Proceedings of the 2nd International Conference on Knowledge Discovery
    and Data Mining, Portland, OR, AAAI Press, pp. 226-231. 1996
    """
    if not eps > 0.0:
        raise ValueError("eps must be positive.")
    if random_state is not None:
        warnings.warn("The parameter random_state is deprecated in 0.16 "
                      "and will be removed in version 0.18. "
                      "DBSCAN is deterministic except for rare border cases.",
                      category=DeprecationWarning)

    X = check_array(X, accept_sparse='csr')
    if sample_weight is not None:
        sample_weight = np.asarray(sample_weight)
        check_consistent_length(X, sample_weight)

    # Calculate neighborhood for all samples. This leaves the original point
    # in, which needs to be considered later (i.e. point i is in the
    # neighborhood of point i. While True, its useless information)
    if metric == 'precomputed':
        D = pairwise_distances(X, metric=metric)
        neighborhoods = np.array([np.where(x <= eps)[0] for x in D])
    else:
        neighbors_model = NearestNeighbors(radius=eps, algorithm=algorithm,
                                           leaf_size=leaf_size,
                                           metric=metric, p=p)
        neighbors_model.fit(X)
        # This has worst case O(n^2) memory complexity
        neighborhoods = neighbors_model.radius_neighbors(X, eps,
                                                         return_distance=False)

    if sample_weight is None:
        n_neighbors = np.array([len(neighbors) for neighbors in neighborhoods])
    else:
        n_neighbors = np.array([np.sum(sample_weight[neighbors])
                                for neighbors in neighborhoods])

    # Initially, all samples are noise.
    labels = -np.ones(X.shape[0], dtype=np.intp)

    # A list of all core samples found.
    core_samples = np.asarray(n_neighbors >= min_samples, dtype=np.uint8)
    dbscan_inner(core_samples, neighborhoods, labels)
    return np.where(core_samples)[0], labels