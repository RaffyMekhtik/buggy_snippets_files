def _minimize_trustregion_constr(fun, x0, args, grad,
                                 hess, hessp, bounds, constraints,
                                 xtol=1e-8, gtol=1e-8,
                                 barrier_tol=1e-8,
                                 sparse_jacobian=None,
                                 callback=None, maxiter=1000,
                                 verbose=0, finite_diff_rel_step=None,
                                 initial_constr_penalty=1.0, initial_tr_radius=1.0,
                                 initial_barrier_parameter=0.1,
                                 initial_barrier_tolerance=0.1,
                                 factorization_method=None,
                                 disp=False):
    """Minimize a scalar function subject to constraints.

    Parameters
    ----------
    gtol : float, optional
        Tolerance for termination by the norm of the Lagrangian gradient.
        The algorithm will terminate when both the infinity norm (i.e. max
        abs value) of the Lagrangian gradient and the constraint violation
        are smaller than ``gtol``. Default is 1e-8.
    xtol : float, optional
        Tolerance for termination by the change of the independent variable.
        The algorithm will terminate when ``tr_radius < xtol``, where
        ``tr_radius`` is the radius of the trust region used in the algorithm.
        Default is 1e-8.
    barrier_tol : float, optional
        Threshold on the barrier parameter for the algorithm termination.
        When inequality constraints are present the algorithm will terminate
        only when the barrier parameter is less than `barrier_tol`.
        Default is 1e-8.
    sparse_jacobian : {bool, None}, optional
        Determines how to represent Jacobians of the constraints. If bool,
        then Jacobians of all the constraints will be converted to the
        corresponding format. If None (default), then Jacobians won't be
        converted, but the algorithm can proceed only if they all have the
        same format.
    initial_tr_radius: float, optional
        Initial trust radius. The trust radius gives the maximum distance
        between solution points in consecutive iterations. It reflects the
        trust the algorithm puts in the local approximation of the optimization
        problem. For an accurate local approximation the trust-region should be
        large and for an  approximation valid only close to the current point it
        should be a small one. The trust radius is automatically updated throughout
        the optimization process, with ``initial_tr_radius`` being its initial value.
        Default is 1 (recommended in [1]_, p. 19).
    initial_constr_penalty : float, optional
        Initial constraints penalty parameter. The penalty parameter is used for
        balancing the requirements of decreasing the objective function
        and satisfying the constraints. It is used for defining the merit function:
        ``merit_function(x) = fun(x) + constr_penalty * constr_norm_l2(x)``,
        where ``constr_norm_l2(x)`` is the l2 norm of a vector containing all
        the constraints. The merit function is used for accepting or rejecting
        trial points and ``constr_penalty`` weights the two conflicting goals
        of reducing objective function and constraints. The penalty is automatically
        updated throughout the optimization  process, with
        ``initial_constr_penalty`` being its  initial value. Default is 1
        (recommended in [1]_, p 19).
    initial_barrier_parameter, initial_barrier_tolerance: float, optional
        Initial barrier parameter and initial tolerance for the barrier subproblem.
        Both are used only when inequality constraints are present. For dealing with
        optimization problems ``min_x f(x)`` subject to inequality constraints
        ``c(x) <= 0`` the algorithm introduces slack variables, solving the problem
        ``min_(x,s) f(x) + barrier_parameter*sum(ln(s))`` subject to the equality
        constraints  ``c(x) + s = 0`` instead of the original problem. This subproblem
        is solved for increasing values of ``barrier_parameter`` and with decreasing
        tolerances for the termination, starting with ``initial_barrier_parameter``
        for the barrier parameter and ``initial_barrier_tolerance`` for the
        barrier subproblem  barrier. Default is 0.1 for both values (recommended in [1]_ p. 19).
    factorization_method : string or None, optional
        Method to factorize the Jacobian of the constraints. Use None (default)
        for the auto selection or one of:

            - 'NormalEquation' (requires scikit-sparse)
            - 'AugmentedSystem'
            - 'QRFactorization'
            - 'SVDFactorization'

        The methods 'NormalEquation' and 'AugmentedSystem' can be used only
        with sparse constraints. The projections required by the algorithm
        will be computed using, respectively, the the normal equation  and the
        augmented system approaches explained in [1]_. 'NormalEquation'
        computes the Cholesky factorization of ``A A.T`` and 'AugmentedSystem'
        performs the LU factorization of an augmented system. They usually
        provide similar results. 'AugmentedSystem' is used by default for
        sparse matrices.

        The methods 'QRFactorization' and 'SVDFactorization' can be used
        only with dense constraints. They compute the required projections
        using, respectively, QR and SVD factorizations. The 'SVDFactorization'
        method can cope with Jacobian matrices with deficient row rank and will
        be used whenever other factorization methods fail (which may imply the
        conversion of sparse matrices to a dense format when required).
        By default 'QRFactorization' is used for dense matrices.
    finite_diff_rel_step : None or array_like, optional
        Relative step size for the finite difference approximation.
    maxiter : int, optional
        Maximum number of algorithm iterations. Default is 1000.
    verbose : {0, 1, 2}, optional
        Level of algorithm's verbosity:

            * 0 (default) : work silently.
            * 1 : display a termination report.
            * 2 : display progress during iterations.
            * 3 : display progress during iterations (more complete report).

    disp : bool, optional
        If True (default) then `verbose` will be set to 1 if it was 0.

    Returns
    -------
    `OptimizeResult` with the fields documented below. Note the following:

        1. All values corresponding to the constraints are ordered as they
           were passed to the solver. And values corresponding to `bounds`
           constraints are put *after* other constraints.
        2. All numbers of function, Jacobian or Hessian evaluations correspond
           to numbers of actual Python function calls. It means, for example,
           that if a Jacobian is estimated by finite differences then the
           number of Jacobian evaluations will be zero and the number of
           function evaluations will be incremented by all calls during the
           finite difference estimation.

    x : ndarray, shape (n,)
        Solution found.
    optimality : float
        Infinity norm of the Lagrangian gradient at the solution.
    constr_violation : float
        Maximum constraint violation at the solution.
    fun : float
        Objective function at the solution.
    grad : ndarray, shape (n,)
        Gradient of the objective function at the solution.
    lagrangian_grad : ndarray, shape (n,)
        Gradient of the Lagrangian function at the solution.
    niter : int
        Total number of iterations.
    nfev : integer
        Number of the objective function evaluations.
    ngev : integer
        Number of the objective function gradient evaluations.
    nhev : integer
        Number of the objective function Hessian evaluations.
    cg_niter : int
        Total number of the conjugate gradient method iterations.
    method : {'equality_constrained_sqp', 'tr_interior_point'}
        Optimization method used.    
    constr : list of ndarray
        List of constraint values at the solution.
    jac : list of {ndarray, sparse matrix}
        List of the Jacobian matrices of the constraints at the solution.
    v : list of ndarray
        List of the Lagrange multipliers for the constraints at the solution.
        For an inequality constraint a positive multiplier means that the upper
        bound is active, a negative multiplier means that the lower bound is
        active and if a multiplier is zero it means the constraint is not
        active.
    constr_nfev : list of int
        Number of constraint evaluations for each of the constraints.
    constr_njev : list of int
        Number of Jacobian matrix evaluations for each of the constraints.
    constr_nhev : list of int
        Number of Hessian evaluations for each of the constraints.
    tr_radius : float
        Radius of the trust region at the last iteration.
    constr_penalty : float
        Penalty parameter at the last iteration, see `initial_constr_penalty`.
    barrier_tolerance : float
        Tolerance for the barrier subproblem at the last iteration.
        Only for problems with inequality constraints.
    barrier_parameter : float
        Barrier parameter at the last iteration. Only for problems
        with inequality constraints.
    execution_time : float
        Total execution time.
    message : str
        Termination message.
    status : {0, 1, 2, 3}
        Termination status:

            * 0 : The maximum number of function evaluations is exceeded.
            * 1 : `gtol` termination condition is satisfied.
            * 2 : `xtol` termination condition is satisfied.
            * 3 : `callback` function requested termination.

    cg_stop_cond : int
        Reason for CG subproblem termination at the last iteration:

            * 0 : CG subproblem not evaluated.
            * 1 : Iteration limit was reached.
            * 2 : Reached the trust-region boundary.
            * 3 : Negative curvature detected.
            * 4 : Tolerance was satisfied.
    """
    x0 = np.atleast_1d(x0).astype(float)
    n_vars = np.size(x0)
    if hess is None:
        if callable(hessp):
            hess = HessianLinearOperator(hessp, n_vars)
        else:
            hess = BFGS()
    if disp and verbose == 0:
        verbose = 1

    if bounds is not None:
        finite_diff_bounds = strict_bounds(bounds.lb, bounds.ub,
                                           bounds.keep_feasible, n_vars)
    else:
        finite_diff_bounds = (-np.inf, np.inf)

    # Define Objective Function
    objective = ScalarFunction(fun, x0, args, grad, hess,
                               finite_diff_rel_step, finite_diff_bounds)

    # Put constraints in list format when needed
    if isinstance(constraints, (NonlinearConstraint, LinearConstraint)):
        constraints = [constraints]

    # Prepare constraints.
    prepared_constraints = [
        PreparedConstraint(c, x0, sparse_jacobian, finite_diff_bounds)
        for c in constraints]

    # Check that all constraints are either sparse or dense.
    n_sparse = sum(c.fun.sparse_jacobian for c in prepared_constraints)
    if 0 < n_sparse < len(prepared_constraints):
        raise ValueError("All constraints must have the same kind of the "
                         "Jacobian --- either all sparse or all dense. "
                         "You can set the sparsity globally by setting "
                         "`sparse_jacobian` to either True of False.")
    if prepared_constraints:
        sparse_jacobian = n_sparse > 0

    if bounds is not None:
        if sparse_jacobian is None:
            sparse_jacobian = True
        prepared_constraints.append(PreparedConstraint(bounds, x0,
                                                       sparse_jacobian))

    # Concatenate initial constraints to the canonical form.
    c_eq0, c_ineq0, J_eq0, J_ineq0 = initial_constraints_as_canonical(
        n_vars, prepared_constraints, sparse_jacobian)

    # Prepare all canonical constraints and concatenate it into one.
    canonical_all = [CanonicalConstraint.from_PreparedConstraint(c)
                     for c in prepared_constraints]

    if len(canonical_all) == 0:
        canonical = CanonicalConstraint.empty(n_vars)
    elif len(canonical_all) == 1:
        canonical = canonical_all[0]
    else:
        canonical = CanonicalConstraint.concatenate(canonical_all,
                                                    sparse_jacobian)

    # Generate the Hessian of the Lagrangian.
    lagrangian_hess = LagrangianHessian(n_vars, objective.hess, canonical.hess)

    # Choose appropriate method
    if canonical.n_ineq == 0:
        method = 'equality_constrained_sqp'
    else:
        method = 'tr_interior_point'

    # Construct OptimizeResult
    state = OptimizeResult(
        niter=0, nfev=0, njev=0, nhev=0,
        cg_niter=0, cg_stop_cond=0,
        fun=objective.f, grad=objective.g,
        lagrangian_grad=np.copy(objective.g),
        constr=[c.fun.f for c in prepared_constraints],
        jac=[c.fun.J for c in prepared_constraints],
        constr_nfev=[0 for c in prepared_constraints],
        constr_njev=[0 for c in prepared_constraints],
        constr_nhev=[0 for c in prepared_constraints],
        v=[c.fun.v for c in prepared_constraints],
        method=method)

    # Start counting
    start_time = time.time()

    # Define stop criteria
    if method == 'equality_constrained_sqp':
        def stop_criteria(state, x, last_iteration_failed,
                          optimality, constr_violation,
                          tr_radius, constr_penalty, cg_info):
            state = update_state_sqp(state, x, last_iteration_failed,
                                     objective, prepared_constraints,
                                     start_time, tr_radius, constr_penalty,
                                     cg_info)
            if verbose == 2:
                BasicReport.print_iteration(state.niter,
                                            state.nfev,
                                            state.cg_niter,
                                            state.fun,
                                            state.tr_radius,
                                            state.optimality,
                                            state.constr_violation)
            elif verbose > 2:
                SQPReport.print_iteration(state.niter,
                                          state.nfev,
                                          state.cg_niter,
                                          state.fun,
                                          state.tr_radius,
                                          state.optimality,
                                          state.constr_violation,
                                          state.constr_penalty,
                                          state.cg_stop_cond)
            state.status = None
            if callback is not None and callback(np.copy(state.x), state):
                state.status = 3
            elif state.optimality < gtol and state.constr_violation < gtol:
                state.status = 1
            elif state.tr_radius < xtol:
                state.status = 2
            elif state.niter > maxiter:
                state.status = 0
            return state.status in (0, 1, 2, 3)
    elif method == 'tr_interior_point':
        def stop_criteria(state, x, last_iteration_failed, tr_radius,
                          constr_penalty, cg_info, barrier_parameter,
                          barrier_tolerance):
            state = update_state_ip(state, x, last_iteration_failed,
                                    objective, prepared_constraints,
                                    start_time, tr_radius, constr_penalty,
                                    cg_info, barrier_parameter, barrier_tolerance)
            if verbose == 2:
                BasicReport.print_iteration(state.niter,
                                            state.nfev,
                                            state.cg_niter,
                                            state.fun,
                                            state.tr_radius,
                                            state.optimality,
                                            state.constr_violation)
            elif verbose > 2:
                IPReport.print_iteration(state.niter,
                                         state.nfev,
                                         state.cg_niter,
                                         state.fun,
                                         state.tr_radius,
                                         state.optimality,
                                         state.constr_violation,
                                         state.constr_penalty,
                                         state.barrier_parameter,
                                         state.cg_stop_cond)
            state.status = None
            if callback is not None and callback(np.copy(state.x), state):
                state.status = 3
            elif state.optimality < gtol and state.constr_violation < gtol:
                state.status = 1
            elif (state.tr_radius < xtol
                  and state.barrier_parameter < barrier_tol):
                state.status = 2
            elif state.niter > maxiter:
                state.status = 0
            return state.status in (0, 1, 2, 3)

    if verbose == 2:
        BasicReport.print_header()
    elif verbose > 2:
        if method == 'equality_constrained_sqp':
            SQPReport.print_header()
        elif method == 'tr_interior_point':
            IPReport.print_header()

    # Call inferior function to do the optimization
    if method == 'equality_constrained_sqp':
        def fun_and_constr(x):
            f = objective.fun(x)
            c_eq, _ = canonical.fun(x)
            return f, c_eq

        def grad_and_jac(x):
            g = objective.grad(x)
            J_eq, _ = canonical.jac(x)
            return g, J_eq

        _, result = equality_constrained_sqp(
            fun_and_constr, grad_and_jac, lagrangian_hess,
            x0, objective.f, objective.g,
            c_eq0, J_eq0,
            stop_criteria, state,
            initial_constr_penalty, initial_tr_radius,
            factorization_method)

    elif method == 'tr_interior_point':
        _, result = tr_interior_point(
            objective.fun, objective.grad, lagrangian_hess,
            n_vars, canonical.n_ineq, canonical.n_eq,
            canonical.fun, canonical.jac,
            x0, objective.f, objective.g,
            c_ineq0, J_ineq0, c_eq0, J_eq0,
            stop_criteria,
            canonical.keep_feasible,
            xtol, state, initial_barrier_parameter,
            initial_barrier_tolerance,
            initial_constr_penalty, initial_tr_radius,
            factorization_method)

    result.message = TERMINATION_MESSAGES[result.status]

    if verbose == 2:
        BasicReport.print_footer()
    elif verbose > 2:
        if method == 'equality_constrained_sqp':
            SQPReport.print_footer()
        elif method == 'tr_interior_point':
            IPReport.print_footer()
    if verbose >= 1:
        print(result.message)
        print("Number of iterations: {}, function evaluations: {}, "
              "CG iterations: {}, optimality: {:.2e}, "
              "constraint violation: {:.2e}, execution time: {:4.2} s."
              .format(result.niter, result.nfev, result.cg_niter,
                      result.optimality, result.constr_violation,
                      result.execution_time))
    return result