def distance_metrics():
    """Valid metrics for pairwise_distances.

    This function simply returns the valid pairwise distance metrics.
    It exists to allow for a description of the mapping for
    each of the valid strings.

    The valid distance metrics, and the function they map to, are:

    ============     ====================================
    metric           Function
    ============     ====================================
    'cityblock'      metrics.pairwise.manhattan_distances
    'cosine'         metrics.pairwise.cosine_distances
    'euclidean'      metrics.pairwise.euclidean_distances
    'haversine'      metrics.pairwise.haversine_distances
    'l1'             metrics.pairwise.manhattan_distances
    'l2'             metrics.pairwise.euclidean_distances
    'manhattan'      metrics.pairwise.manhattan_distances
    ============     ====================================

    Read more in the :ref:`User Guide <metrics>`.

    """
    return PAIRWISE_DISTANCE_FUNCTIONS