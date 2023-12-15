def quantileTS(frame, percentile):
    """
    Return score at percentile for each point in time (cross-section)

    Parameters
    ----------
    frame: DataFrame
    percentile: int
       nth percentile

    See also
    --------
    scipy.stats.scoreatpercentile

    Returns
    -------
    Series (or TimeSeries)
    """
    from scipy.stats import scoreatpercentile

    def func(x):
        x = np.asarray(x.valid())
        if x.any():
            return scoreatpercentile(x, percentile)
        else:
            return NaN
    return frame.apply(func, axis=1)