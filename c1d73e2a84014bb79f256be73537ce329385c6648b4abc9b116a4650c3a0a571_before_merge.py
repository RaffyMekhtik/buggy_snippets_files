def scatter_matrix(frame, alpha=0.5, figsize=None, ax=None, grid=False,
                   diagonal='hist', marker='.', density_kwds=None,
                   hist_kwds=None, range_padding=0.05, **kwds):
    """
    Draw a matrix of scatter plots.

    Parameters
    ----------
    frame : DataFrame
    alpha : float, optional
        amount of transparency applied
    figsize : (float,float), optional
        a tuple (width, height) in inches
    ax : Matplotlib axis object, optional
    grid : bool, optional
        setting this to True will show the grid
    diagonal : {'hist', 'kde'}
        pick between 'kde' and 'hist' for
        either Kernel Density Estimation or Histogram
        plot in the diagonal
    marker : str, optional
        Matplotlib marker type, default '.'
    hist_kwds : other plotting keyword arguments
        To be passed to hist function
    density_kwds : other plotting keyword arguments
        To be passed to kernel density estimate plot
    range_padding : float, optional
        relative extension of axis range in x and y
        with respect to (x_max - x_min) or (y_max - y_min),
        default 0.05
    kwds : other plotting keyword arguments
        To be passed to scatter function

    Examples
    --------
    >>> df = DataFrame(np.random.randn(1000, 4), columns=['A','B','C','D'])
    >>> scatter_matrix(df, alpha=0.2)
    """
    import matplotlib.pyplot as plt

    df = frame._get_numeric_data()
    n = df.columns.size
    naxes = n * n
    fig, axes = _subplots(naxes=naxes, figsize=figsize, ax=ax,
                          squeeze=False)

    # no gaps between subplots
    fig.subplots_adjust(wspace=0, hspace=0)

    mask = notnull(df)

    marker = _get_marker_compat(marker)

    hist_kwds = hist_kwds or {}
    density_kwds = density_kwds or {}

    # workaround because `c='b'` is hardcoded in matplotlibs scatter method
    kwds.setdefault('c', plt.rcParams['patch.facecolor'])

    boundaries_list = []
    for a in df.columns:
        values = df[a].values[mask[a].values]
        rmin_, rmax_ = np.min(values), np.max(values)
        rdelta_ext = (rmax_ - rmin_) * range_padding / 2.
        boundaries_list.append((rmin_ - rdelta_ext, rmax_ + rdelta_ext))

    for i, a in zip(lrange(n), df.columns):
        for j, b in zip(lrange(n), df.columns):
            ax = axes[i, j]

            if i == j:
                values = df[a].values[mask[a].values]

                # Deal with the diagonal by drawing a histogram there.
                if diagonal == 'hist':
                    ax.hist(values, **hist_kwds)

                elif diagonal in ('kde', 'density'):
                    from scipy.stats import gaussian_kde
                    y = values
                    gkde = gaussian_kde(y)
                    ind = np.linspace(y.min(), y.max(), 1000)
                    ax.plot(ind, gkde.evaluate(ind), **density_kwds)

                ax.set_xlim(boundaries_list[i])

            else:
                common = (mask[a] & mask[b]).values

                ax.scatter(df[b][common], df[a][common],
                           marker=marker, alpha=alpha, **kwds)

                ax.set_xlim(boundaries_list[j])
                ax.set_ylim(boundaries_list[i])

            ax.set_xlabel(b)
            ax.set_ylabel(a)

            if j != 0:
                ax.yaxis.set_visible(False)
            if i != n - 1:
                ax.xaxis.set_visible(False)

    if len(df.columns) > 1:
        lim1 = boundaries_list[0]
        locs = axes[0][1].yaxis.get_majorticklocs()
        locs = locs[(lim1[0] <= locs) & (locs <= lim1[1])]
        adj = (locs - lim1[0]) / (lim1[1] - lim1[0])

        lim0 = axes[0][0].get_ylim()
        adj = adj * (lim0[1] - lim0[0]) + lim0[0]
        axes[0][0].yaxis.set_ticks(adj)

        if np.all(locs == locs.astype(int)):
            # if all ticks are int
            locs = locs.astype(int)
        axes[0][0].yaxis.set_ticklabels(locs)

    _set_ticks_props(axes, xlabelsize=8, xrot=90, ylabelsize=8, yrot=0)

    return axes