def louvain(
    adata: AnnData,
    resolution: Optional[float] = None,
    random_state: Optional[Union[int, RandomState]] = 0,
    restrict_to: Optional[Tuple[str, Sequence[str]]] = None,
    key_added: str = 'louvain',
    adjacency: Optional[spmatrix] = None,
    flavor: Literal['vtraag', 'igraph', 'rapids'] = 'vtraag',
    directed: bool = True,
    use_weights: bool = False,
    partition_type: Optional[Type[MutableVertexPartition]] = None,
    partition_kwargs: Mapping[str, Any] = MappingProxyType({}),
    copy: bool = False,
) -> Optional[AnnData]:
    """\
    Cluster cells into subgroups [Blondel08]_ [Levine15]_ [Traag17]_.

    Cluster cells using the Louvain algorithm [Blondel08]_ in the implementation
    of [Traag17]_. The Louvain algorithm has been proposed for single-cell
    analysis by [Levine15]_.

    This requires having ran :func:`~scanpy.pp.neighbors` or
    :func:`~scanpy.external.pp.bbknn` first,
    or explicitly passing a ``adjacency`` matrix.

    Parameters
    ----------
    adata
        The annotated data matrix.
    resolution
        For the default flavor (``'vtraag'``), you can provide a resolution
        (higher resolution means finding more and smaller clusters),
        which defaults to 1.0.
        See “Time as a resolution parameter” in [Lambiotte09]_.
    random_state
        Change the initialization of the optimization.
    restrict_to
        Restrict the clustering to the categories within the key for sample
        annotation, tuple needs to contain ``(obs_key, list_of_categories)``.
    key_added
        Key under which to add the cluster labels. (default: ``'louvain'``)
    adjacency
        Sparse adjacency matrix of the graph, defaults to
        ``adata.uns['neighbors']['connectivities']``.
    flavor
        Choose between to packages for computing the clustering.
        ``'vtraag'`` is much more powerful, and the default.
    directed
        Interpret the ``adjacency`` matrix as directed graph?
    use_weights
        Use weights from knn graph.
    partition_type
        Type of partition to use.
        Only a valid argument if ``flavor`` is ``'vtraag'``.
    partition_kwargs
        Key word arguments to pass to partitioning,
        if ``vtraag`` method is being used.
    copy
        Copy adata or modify it inplace.

    Returns
    -------
    :obj:`None`
        By default (``copy=False``), updates ``adata`` with the following fields:

        ``adata.obs['louvain']`` (:class:`pandas.Series`, dtype ``category``)
            Array of dim (number of samples) that stores the subgroup id
            (``'0'``, ``'1'``, ...) for each cell.

    :class:`~anndata.AnnData`
        When ``copy=True`` is set, a copy of ``adata`` with those fields is returned.
    """
    partition_kwargs = dict(partition_kwargs)
    start = logg.info('running Louvain clustering')
    if (flavor != 'vtraag') and (partition_type is not None):
        raise ValueError(
            '`partition_type` is only a valid argument '
            'when `flavour` is "vtraag"'
        )
    adata = adata.copy() if copy else adata
    if adjacency is None and 'neighbors' not in adata.uns:
        raise ValueError(
            'You need to run `pp.neighbors` first '
            'to compute a neighborhood graph.'
        )
    if adjacency is None:
        adjacency = adata.uns['neighbors']['connectivities']
    if restrict_to is not None:
        restrict_key, restrict_categories = restrict_to
        adjacency, restrict_indices = restrict_adjacency(
            adata,
            restrict_key,
            restrict_categories,
            adjacency,
        )
    if flavor in {'vtraag', 'igraph'}:
        if flavor == 'igraph' and resolution is not None:
            logg.warning(
                '`resolution` parameter has no effect for flavor "igraph"'
            )
        if directed and flavor == 'igraph':
            directed = False
        if not directed: logg.debug('    using the undirected graph')
        g = _utils.get_igraph_from_adjacency(adjacency, directed=directed)
        if use_weights:
            weights = np.array(g.es["weight"]).astype(np.float64)
        else:
            weights = None
        if flavor == 'vtraag':
            import louvain
            if partition_type is None:
                partition_type = louvain.RBConfigurationVertexPartition
            if resolution is not None:
                partition_kwargs["resolution_parameter"] = resolution
            if use_weights:
                partition_kwargs["weights"] = weights
            logg.info('    using the "louvain" package of Traag (2017)')
            louvain.set_rng_seed(random_state)
            part = louvain.find_partition(
                g, partition_type,
                **partition_kwargs,
            )
            # adata.uns['louvain_quality'] = part.quality()
        else:
            part = g.community_multilevel(weights=weights)
        groups = np.array(part.membership)
    elif flavor == 'rapids':
        # nvLouvain only works with undirected graphs,
        # and `adjacency` must have a directed edge in both directions
        import cudf
        import cugraph
        offsets = cudf.Series(adjacency.indptr)
        indices = cudf.Series(adjacency.indices)
        if use_weights:
            sources, targets = adjacency.nonzero()
            weights = adjacency[sources, targets]
            if isinstance(weights, np.matrix):
                weights = weights.A1
            weights = cudf.Series(weights)
        else:
            weights = None
        g = cugraph.Graph()
        g.add_adj_list(offsets, indices, weights)
        logg.info('    using the "louvain" package of rapids')
        louvain_parts, _ = cugraph.nvLouvain(g)
        groups = louvain_parts.to_pandas().sort_values('vertex')[['partition']].to_numpy().ravel()
    elif flavor == 'taynaud':
        # this is deprecated
        import networkx as nx
        import community
        g = nx.Graph(adjacency)
        partition = community.best_partition(g)
        groups = np.zeros(len(partition), dtype=int)
        for k, v in partition.items(): groups[k] = v
    else:
        raise ValueError(
            '`flavor` needs to be "vtraag" or "igraph" or "taynaud".'
        )
    if restrict_to is not None:
        if key_added == 'louvain':
            key_added += '_R'
        groups = rename_groups(
            adata,
            key_added,
            restrict_key,
            restrict_categories,
            restrict_indices,
            groups,
        )
    adata.obs[key_added] = pd.Categorical(
        values=groups.astype('U'),
        categories=natsorted(map(str, np.unique(groups))),
    )
    adata.uns['louvain'] = {}
    adata.uns['louvain']['params'] = dict(
        resolution=resolution,
        random_state=random_state,
    )
    logg.info(
        '    finished',
        time=start,
        deep=(
            f'found {len(np.unique(groups))} clusters and added\n'
            f'    {key_added!r}, the cluster labels (adata.obs, categorical)'
        ),
    )
    return adata if copy else None