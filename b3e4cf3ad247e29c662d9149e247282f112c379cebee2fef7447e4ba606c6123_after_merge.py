def plot_tfr_topomap(tfr, tmin=None, tmax=None, fmin=None, fmax=None,
                     ch_type=None, baseline=None, mode='mean', layout=None,
                     vmin=None, vmax=None, cmap=None, sensors=True,
                     colorbar=True, unit=None, res=64, size=2,
                     cbar_fmt='%1.1e', show_names=False, title=None,
                     axes=None, show=True, outlines='head', head_pos=None):
    """Plot topographic maps of specific time-frequency intervals of TFR data

    Parameters
    ----------
    tfr : AvereageTFR
        The AvereageTFR object.
    tmin : None | float
        The first time instant to display. If None the first time point
        available is used.
    tmax : None | float
        The last time instant to display. If None the last time point
        available is used.
    fmin : None | float
        The first frequency to display. If None the first frequency
        available is used.
    fmax : None | float
        The last frequency to display. If None the last frequency
        available is used.
    ch_type : 'mag' | 'grad' | 'planar1' | 'planar2' | 'eeg' | None
        The channel type to plot. For 'grad', the gradiometers are
        collected in pairs and the RMS for each pair is plotted.
        If None, then channels are chosen in the order given above.
    baseline : tuple or list of length 2
        The time interval to apply rescaling / baseline correction.
        If None do not apply it. If baseline is (a, b)
        the interval is between "a (s)" and "b (s)".
        If a is None the beginning of the data is used
        and if b is None then b is set to the end of the interval.
        If baseline is equal to (None, None) all the time
        interval is used.
    mode : 'logratio' | 'ratio' | 'zscore' | 'mean' | 'percent'
        Do baseline correction with ratio (power is divided by mean
        power during baseline) or z-score (power is divided by standard
        deviation of power during baseline after subtracting the mean,
        power = [power - mean(power_baseline)] / std(power_baseline))
        If None, baseline no correction will be performed.
    layout : None | Layout
        Layout instance specifying sensor positions (does not need to
        be specified for Neuromag data). If possible, the correct layout
        file is inferred from the data; if no appropriate layout file
        was found, the layout is automatically generated from the sensor
        locations.
    vmin : float | callable | None
        The value specifying the lower bound of the color range.
        If None, and vmax is None, -vmax is used. Else np.min(data) or in case
        data contains only positive values 0. If callable, the output equals
        vmin(data). Defaults to None.
    vmax : float | callable | None
        The value specifying the upper bound of the color range. If None, the
        maximum value is used. If callable, the output equals vmax(data).
        Defaults to None.
    cmap : matplotlib colormap | (colormap, bool) | 'interactive' | None
        Colormap to use. If tuple, the first value indicates the colormap to
        use and the second value is a boolean defining interactivity. In
        interactive mode the colors are adjustable by clicking and dragging the
        colorbar with left and right mouse button. Left mouse button moves the
        scale up and down and right mouse button adjusts the range. Hitting
        space bar resets the range. Up and down arrows can be used to change
        the colormap. If None (default), 'Reds' is used for all positive data,
        otherwise defaults to 'RdBu_r'. If 'interactive', translates to
        (None, True).
    sensors : bool | str
        Add markers for sensor locations to the plot. Accepts matplotlib
        plot format string (e.g., 'r+' for red plusses). If True, a circle will
        be used (via .add_artist). Defaults to True.
    colorbar : bool
        Plot a colorbar.
    unit : str | None
        The unit of the channel type used for colorbar labels.
    res : int
        The resolution of the topomap image (n pixels along each side).
    size : float
        Side length per topomap in inches.
    cbar_fmt : str
        String format for colorbar values.
    show_names : bool | callable
        If True, show channel names on top of the map. If a callable is
        passed, channel names will be formatted using the callable; e.g., to
        delete the prefix 'MEG ' from all channel names, pass the function
        lambda x: x.replace('MEG ', ''). If `mask` is not None, only
        significant sensors will be shown.
    title : str | None
        Title. If None (default), no title is displayed.
    axes : instance of Axis | None
        The axes to plot to. If None the axes is defined automatically.
    show : bool
        Show figure if True.
    outlines : 'head' | 'skirt' | dict | None
        The outlines to be drawn. If 'head', the default head scheme will be
        drawn. If 'skirt' the head scheme will be drawn, but sensors are
        allowed to be plotted outside of the head circle. If dict, each key
        refers to a tuple of x and y positions, the values in 'mask_pos' will
        serve as image mask, and the 'autoshrink' (bool) field will trigger
        automated shrinking of the positions due to points outside the outline.
        Alternatively, a matplotlib patch object can be passed for advanced
        masking options, either directly or as a function that returns patches
        (required for multi-axis plots). If None, nothing will be drawn.
        Defaults to 'head'.
    head_pos : dict | None
        If None (default), the sensors are positioned such that they span
        the head circle. If dict, can have entries 'center' (tuple) and
        'scale' (tuple) for what the center and scale of the head should be
        relative to the electrode locations.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The figure containing the topography.
    """
    from ..channels import _get_ch_type
    ch_type = _get_ch_type(tfr, ch_type)
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    picks, pos, merge_grads, names, _ = _prepare_topo_plot(tfr, ch_type,
                                                           layout)
    if not show_names:
        names = None

    data = tfr.data
    data = rescale(data, tfr.times, baseline, mode, copy=True)

    # crop time
    itmin, itmax = None, None
    idx = np.where(_time_mask(tfr.times, tmin, tmax))[0]
    if tmin is not None:
        itmin = idx[0]
    if tmax is not None:
        itmax = idx[-1] + 1

    # crop freqs
    ifmin, ifmax = None, None
    idx = np.where(_time_mask(tfr.freqs, fmin, fmax))[0]
    if fmin is not None:
        ifmin = idx[0]
    if fmax is not None:
        ifmax = idx[-1] + 1

    data = data[picks, ifmin:ifmax, itmin:itmax]
    data = np.mean(np.mean(data, axis=2), axis=1)[:, np.newaxis]

    if merge_grads:
        from ..channels.layout import _merge_grad_data
        data = _merge_grad_data(data)

    norm = False if np.min(data) < 0 else True
    vmin, vmax = _setup_vmin_vmax(data, vmin, vmax, norm)
    if cmap is None or cmap == 'interactive':
        cmap = ('Reds', True) if norm else ('RdBu_r', True)
    elif not isinstance(cmap, tuple):
        cmap = (cmap, True)

    if axes is None:
        fig = plt.figure()
        ax = fig.gca()
    else:
        fig = axes.figure
        ax = axes

    _hide_frame(ax)

    if title is not None:
        ax.set_title(title)
    fig_wrapper = list()
    selection_callback = partial(_onselect, tfr=tfr, pos=pos, ch_type=ch_type,
                                 itmin=itmin, itmax=itmax, ifmin=ifmin,
                                 ifmax=ifmax, cmap=cmap[0], fig=fig_wrapper,
                                 layout=layout)

    im, _ = plot_topomap(data[:, 0], pos, vmin=vmin, vmax=vmax,
                         axes=ax, cmap=cmap[0], image_interp='bilinear',
                         contours=False, names=names, show_names=show_names,
                         show=False, onselect=selection_callback)

    if colorbar:
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cbar = plt.colorbar(im, cax=cax, format=cbar_fmt, cmap=cmap[0])
        cbar.set_ticks((vmin, vmax))
        cbar.ax.tick_params(labelsize=12)
        cbar.ax.set_title('AU')
        if cmap[1]:
            ax.CB = DraggableColorbar(cbar, im)

    plt_show(show)
    return fig