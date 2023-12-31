def approx_derivative(fun, x0, method='3-point', rel_step=None, f0=None,
                      bounds=(-np.inf, np.inf), sparsity=None,
                      as_linear_operator=False, args=(), kwargs={}):
    """Compute finite difference approximation of the derivatives of a
    vector-valued function.

    If a function maps from R^n to R^m, its derivatives form m-by-n matrix
    called the Jacobian, where an element (i, j) is a partial derivative of
    f[i] with respect to x[j].

    Parameters
    ----------
    fun : callable
        Function of which to estimate the derivatives. The argument x
        passed to this function is ndarray of shape (n,) (never a scalar
        even if n=1). It must return 1-D array_like of shape (m,) or a scalar.
    x0 : array_like of shape (n,) or float
        Point at which to estimate the derivatives. Float will be converted
        to a 1-D array.
    method : {'3-point', '2-point', 'cs'}, optional
        Finite difference method to use:
            - '2-point' - use the first order accuracy forward or backward
                          difference.
            - '3-point' - use central difference in interior points and the
                          second order accuracy forward or backward difference
                          near the boundary.
            - 'cs' - use a complex-step finite difference scheme. This assumes
                     that the user function is real-valued and can be
                     analytically continued to the complex plane. Otherwise,
                     produces bogus results.
    rel_step : None or array_like, optional
        Relative step size to use. The absolute step size is computed as
        ``h = rel_step * sign(x0) * max(1, abs(x0))``, possibly adjusted to
        fit into the bounds. For ``method='3-point'`` the sign of `h` is
        ignored. If None (default) then step is selected automatically,
        see Notes.
    f0 : None or array_like, optional
        If not None it is assumed to be equal to ``fun(x0)``, in  this case
        the ``fun(x0)`` is not called. Default is None.
    bounds : tuple of array_like, optional
        Lower and upper bounds on independent variables. Defaults to no bounds.
        Each bound must match the size of `x0` or be a scalar, in the latter
        case the bound will be the same for all variables. Use it to limit the
        range of function evaluation. Bounds checking is not implemented
        when `as_linear_operator` is True.
    sparsity : {None, array_like, sparse matrix, 2-tuple}, optional
        Defines a sparsity structure of the Jacobian matrix. If the Jacobian
        matrix is known to have only few non-zero elements in each row, then
        it's possible to estimate its several columns by a single function
        evaluation [3]_. To perform such economic computations two ingredients
        are required:

        * structure : array_like or sparse matrix of shape (m, n). A zero
          element means that a corresponding element of the Jacobian
          identically equals to zero.
        * groups : array_like of shape (n,). A column grouping for a given
          sparsity structure, use `group_columns` to obtain it.

        A single array or a sparse matrix is interpreted as a sparsity
        structure, and groups are computed inside the function. A tuple is
        interpreted as (structure, groups). If None (default), a standard
        dense differencing will be used.

        Note, that sparse differencing makes sense only for large Jacobian
        matrices where each row contains few non-zero elements.
    as_linear_operator : bool, optional
        When True the function returns an `scipy.sparse.linalg.LinearOperator`.
        Otherwise it returns a dense array or a sparse matrix depending on
        `sparsity`. The linear operator provides an efficient way of computing
        ``J.dot(p)`` for any vector ``p`` of shape (n,), but does not allow
        direct access to individual elements of the matrix. By default
        `as_linear_operator` is False.
    args, kwargs : tuple and dict, optional
        Additional arguments passed to `fun`. Both empty by default.
        The calling signature is ``fun(x, *args, **kwargs)``.

    Returns
    -------
    J : {ndarray, sparse matrix, LinearOperator}
        Finite difference approximation of the Jacobian matrix.
        If `as_linear_operator` is True returns a LinearOperator
        with shape (m, n). Otherwise it returns a dense array or sparse
        matrix depending on how `sparsity` is defined. If `sparsity`
        is None then a ndarray with shape (m, n) is returned. If
        `sparsity` is not None returns a csr_matrix with shape (m, n).
        For sparse matrices and linear operators it is always returned as
        a 2-D structure, for ndarrays, if m=1 it is returned
        as a 1-D gradient array with shape (n,).

    See Also
    --------
    check_derivative : Check correctness of a function computing derivatives.

    Notes
    -----
    If `rel_step` is not provided, it assigned to ``EPS**(1/s)``, where EPS is
    machine epsilon for float64 numbers, s=2 for '2-point' method and s=3 for
    '3-point' method. Such relative step approximately minimizes a sum of
    truncation and round-off errors, see [1]_.

    A finite difference scheme for '3-point' method is selected automatically.
    The well-known central difference scheme is used for points sufficiently
    far from the boundary, and 3-point forward or backward scheme is used for
    points near the boundary. Both schemes have the second-order accuracy in
    terms of Taylor expansion. Refer to [2]_ for the formulas of 3-point
    forward and backward difference schemes.

    For dense differencing when m=1 Jacobian is returned with a shape (n,),
    on the other hand when n=1 Jacobian is returned with a shape (m, 1).
    Our motivation is the following: a) It handles a case of gradient
    computation (m=1) in a conventional way. b) It clearly separates these two
    different cases. b) In all cases np.atleast_2d can be called to get 2-D
    Jacobian with correct dimensions.

    References
    ----------
    .. [1] W. H. Press et. al. "Numerical Recipes. The Art of Scientific
           Computing. 3rd edition", sec. 5.7.

    .. [2] A. Curtis, M. J. D. Powell, and J. Reid, "On the estimation of
           sparse Jacobian matrices", Journal of the Institute of Mathematics
           and its Applications, 13 (1974), pp. 117-120.

    .. [3] B. Fornberg, "Generation of Finite Difference Formulas on
           Arbitrarily Spaced Grids", Mathematics of Computation 51, 1988.

    Examples
    --------
    >>> import numpy as np
    >>> from scipy.optimize import approx_derivative
    >>>
    >>> def f(x, c1, c2):
    ...     return np.array([x[0] * np.sin(c1 * x[1]),
    ...                      x[0] * np.cos(c2 * x[1])])
    ...
    >>> x0 = np.array([1.0, 0.5 * np.pi])
    >>> approx_derivative(f, x0, args=(1, 2))
    array([[ 1.,  0.],
           [-1.,  0.]])

    Bounds can be used to limit the region of function evaluation.
    In the example below we compute left and right derivative at point 1.0.

    >>> def g(x):
    ...     return x**2 if x >= 1 else x
    ...
    >>> x0 = 1.0
    >>> approx_derivative(g, x0, bounds=(-np.inf, 1.0))
    array([ 1.])
    >>> approx_derivative(g, x0, bounds=(1.0, np.inf))
    array([ 2.])
    """
    if method not in ['2-point', '3-point', 'cs']:
        raise ValueError("Unknown method '%s'. " % method)

    x0 = np.atleast_1d(x0)
    if x0.ndim > 1:
        raise ValueError("`x0` must have at most 1 dimension.")

    lb, ub = _prepare_bounds(bounds, x0)

    if lb.shape != x0.shape or ub.shape != x0.shape:
        raise ValueError("Inconsistent shapes between bounds and `x0`.")

    if as_linear_operator and not (np.all(np.isinf(lb))
                                   and np.all(np.isinf(ub))):
        raise ValueError("Bounds not supported when "
                         "`as_linear_operator` is True.")

    def fun_wrapped(x):
        f = np.atleast_1d(fun(x, *args, **kwargs))
        if f.ndim > 1:
            raise RuntimeError("`fun` return value has "
                               "more than 1 dimension.")
        return f

    if f0 is None:
        f0 = fun_wrapped(x0)
    else:
        f0 = np.atleast_1d(f0)
        if f0.ndim > 1:
            raise ValueError("`f0` passed has more than 1 dimension.")

    if np.any((x0 < lb) | (x0 > ub)):
        raise ValueError("`x0` violates bound constraints.")

    if as_linear_operator:
        if rel_step is None:
            rel_step = relative_step[method]

        return _linear_operator_difference(fun_wrapped, x0,
                                           f0, rel_step, method)
    else:
        h = _compute_absolute_step(rel_step, x0, method)

        if method == '2-point':
            h, use_one_sided = _adjust_scheme_to_bounds(
                x0, h, 1, '1-sided', lb, ub)
        elif method == '3-point':
            h, use_one_sided = _adjust_scheme_to_bounds(
                x0, h, 1, '2-sided', lb, ub)
        elif method == 'cs':
            use_one_sided = False

        if sparsity is None:
            return _dense_difference(fun_wrapped, x0, f0, h,
                                     use_one_sided, method)
        else:
            if not issparse(sparsity) and len(sparsity) == 2:
                structure, groups = sparsity
            else:
                structure = sparsity
                groups = group_columns(sparsity)

            if issparse(structure):
                structure = csc_matrix(structure)
            else:
                structure = np.atleast_2d(structure)

            groups = np.atleast_1d(groups)
            return _sparse_difference(fun_wrapped, x0, f0, h,
                                      use_one_sided, structure,
                                      groups, method)