def score_genes(
    adata: AnnData,
    gene_list: Sequence[str],
    ctrl_size: int = 50,
    gene_pool: Optional[Sequence[str]] = None,
    n_bins: int = 25,
    score_name: str = 'score',
    random_state: AnyRandom = 0,
    copy: bool = False,
    use_raw: bool = None,
) -> Optional[AnnData]:
    """\
    Score a set of genes [Satija15]_.

    The score is the average expression of a set of genes subtracted with the
    average expression of a reference set of genes. The reference set is
    randomly sampled from the `gene_pool` for each binned expression value.

    This reproduces the approach in Seurat [Satija15]_ and has been implemented
    for Scanpy by Davide Cittaro.

    Parameters
    ----------
    adata
        The annotated data matrix.
    gene_list
        The list of gene names used for score calculation.
    ctrl_size
        Number of reference genes to be sampled. If `len(gene_list)` is not too
        low, you can set `ctrl_size=len(gene_list)`.
    gene_pool
        Genes for sampling the reference set. Default is all genes.
    n_bins
        Number of expression level bins for sampling.
    score_name
        Name of the field to be added in `.obs`.
    random_state
        The random seed for sampling.
    copy
        Copy `adata` or modify it inplace.
    use_raw
        Use `raw` attribute of `adata` if present.

        .. versionchanged:: 1.4.5
           Default value changed from `False` to `None`.

    Returns
    -------
    Depending on `copy`, returns or updates `adata` with an additional field
    `score_name`.

    Examples
    --------
    See this `notebook <https://github.com/theislab/scanpy_usage/tree/master/180209_cell_cycle>`__.
    """
    start = logg.info(f'computing score {score_name!r}')
    adata = adata.copy() if copy else adata

    if random_state is not None:
        np.random.seed(random_state)

    gene_list_in_var = []
    var_names = adata.raw.var_names if use_raw else adata.var_names
    genes_to_ignore = []
    for gene in gene_list:
        if gene in var_names:
            gene_list_in_var.append(gene)
        else:
            genes_to_ignore.append(gene)
    if len(genes_to_ignore) > 0:
        logg.warning(f'genes are not in var_names and ignored: {genes_to_ignore}')
    gene_list = set(gene_list_in_var[:])

    if len(gene_list) == 0:
        logg.warning('provided gene list has length 0, scores as 0')
        adata.obs[score_name] = 0
        return adata if copy else None

    if gene_pool is None:
        gene_pool = list(var_names)
    else:
        gene_pool = [x for x in gene_pool if x in var_names]

    # Trying here to match the Seurat approach in scoring cells.
    # Basically we need to compare genes against random genes in a matched
    # interval of expression.

    if use_raw is None:
        use_raw = True if adata.raw is not None else False
    _adata = adata.raw if use_raw else adata

    _adata_subset = _adata[:, gene_pool] if len(gene_pool) < len(_adata.var_names) else _adata
    if issparse(_adata_subset.X):
        obs_avg = pd.Series(
            np.array(_adata_subset.X.mean(axis=0)).flatten(), index=gene_pool)  # average expression of genes
    else:
        obs_avg = pd.Series(
            np.nanmean(_adata_subset.X, axis=0), index=gene_pool)  # average expression of genes

    obs_avg = obs_avg[np.isfinite(obs_avg)] # Sometimes (and I don't know how) missing data may be there, with nansfor

    n_items = int(np.round(len(obs_avg) / (n_bins - 1)))
    obs_cut = obs_avg.rank(method='min') // n_items
    control_genes = set()

    # now pick `ctrl_size` genes from every cut
    for cut in np.unique(obs_cut.loc[gene_list]):
        r_genes = np.array(obs_cut[obs_cut == cut].index)
        np.random.shuffle(r_genes)
        # uses full r_genes if ctrl_size > len(r_genes)
        control_genes.update(set(r_genes[:ctrl_size]))

    # To index, we need a list – indexing implies an order.
    control_genes = list(control_genes - gene_list)
    gene_list = list(gene_list)

    X_list = _adata[:, gene_list].X
    if issparse(X_list): X_list = X_list.toarray()
    X_control = _adata[:, control_genes].X
    if issparse(X_control): X_control = X_control.toarray()
    X_control = np.nanmean(X_control, axis=1)

    if len(gene_list) == 0:
        # We shouldn't even get here, but just in case
        logg.hint(
            f'could not add \n'
            f'    {score_name!r}, score of gene set (adata.obs)'
        )
        return adata if copy else None
    elif len(gene_list) == 1:
        if _adata[:, gene_list].X.ndim == 2:
            vector = _adata[:, gene_list].X.toarray()[:, 0] # new anndata
        else:
            vector =  _adata[:, gene_list].X  # old anndata
        score = vector - X_control
    else:
        score = np.nanmean(X_list, axis=1) - X_control

    adata.obs[score_name] = pd.Series(np.array(score).ravel(), index=adata.obs_names)

    logg.info(
        '    finished',
        time=start,
        deep=(
            'added\n'
            f'    {score_name!r}, score of gene set (adata.obs)'
        ),
    )
    return adata if copy else None