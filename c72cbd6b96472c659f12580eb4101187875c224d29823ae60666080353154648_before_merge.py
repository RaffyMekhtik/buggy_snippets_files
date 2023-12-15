def handle_formula_data(Y, X, formula, depth=0, missing='drop'):
    """
    Returns endog, exog, and the model specification from arrays and formula

    Parameters
    ----------
    Y : array-like
        Either endog (the LHS) of a model specification or all of the data.
        Y must define __getitem__ for now.
    X : array-like
        Either exog or None. If all the data for the formula is provided in
        Y then you must explicitly set X to None.
    formula : str or patsy.model_desc
        You can pass a handler by import formula_handler and adding a
        key-value pair where the key is the formula object class and
        the value is a function that returns endog, exog, formula object

    Returns
    -------
    endog : array-like
        Should preserve the input type of Y,X
    exog : array-like
        Should preserve the input type of Y,X. Could be None.
    """
    # half ass attempt to handle other formula objects
    if isinstance(formula, tuple(iterkeys(formula_handler))):
        return formula_handler[type(formula)]

    na_action = NAAction(on_NA=missing)

    if X is not None:
        if data_util._is_using_pandas(Y, X):
            result = dmatrices(formula, (Y, X), depth,
                               return_type='dataframe', NA_action=na_action)
        else:
            result = dmatrices(formula, (Y, X), depth,
                               return_type='dataframe', NA_action=na_action)
    else:
        if data_util._is_using_pandas(Y, None):
            result = dmatrices(formula, Y, depth, return_type='dataframe',
                               NA_action=na_action)
        else:
            result = dmatrices(formula, Y, depth, return_type='dataframe',
                               NA_action=na_action)

    # if missing == 'raise' there's not missing_mask
    missing_mask = getattr(na_action, 'missing_mask', None)
    if not np.any(missing_mask):
        missing_mask = None
    return result, missing_mask