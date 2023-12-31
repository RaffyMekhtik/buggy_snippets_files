def _is_potential_multi_index(
    columns, index_col: Optional[Union[bool, Sequence[int]]] = None
):
    """
    Check whether or not the `columns` parameter
    could be converted into a MultiIndex.

    Parameters
    ----------
    columns : array-like
        Object which may or may not be convertible into a MultiIndex
    index_col : None, bool or list, optional
        Column or columns to use as the (possibly hierarchical) index

    Returns
    -------
    boolean : Whether or not columns could become a MultiIndex
    """
    if index_col is None or isinstance(index_col, bool):
        index_col = []

    return (
        len(columns)
        and not isinstance(columns, MultiIndex)
        and all(isinstance(c, tuple) for c in columns if c not in list(index_col))
    )