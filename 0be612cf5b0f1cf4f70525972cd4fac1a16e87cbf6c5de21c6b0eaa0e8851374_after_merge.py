def _minimize_slsqp(func, x0, args=(), jac=None, bounds=None,
                    constraints=(),
                    maxiter=100, ftol=1.0E-6, iprint=1, disp=False,
                    eps=_epsilon, callback=None, finite_diff_rel_step=None,
                    **unknown_options):
    """
    Minimize a scalar function of one or more variables using Sequential
    Least Squares Programming (SLSQP).

    Options
    -------
    ftol : float
        Precision goal for the value of f in the stopping criterion.
    eps : float
        Step size used for numerical approximation of the Jacobian.
    disp : bool
        Set to True to print convergence messages. If False,
        `verbosity` is ignored and set to 0.
    maxiter : int
        Maximum number of iterations.
    finite_diff_rel_step : None or array_like, optional
        If `jac in ['2-point', '3-point', 'cs']` the relative step size to
        use for numerical approximation of `jac`. The absolute step
        size is computed as ``h = rel_step * sign(x0) * max(1, abs(x0))``,
        possibly adjusted to fit into the bounds. For ``method='3-point'``
        the sign of `h` is ignored. If None (default) then step is selected
        automatically.
    """
    _check_unknown_options(unknown_options)
    iter = maxiter
    acc = ftol
    epsilon = eps

    if not disp:
        iprint = 0

    # Constraints are triaged per type into a dictionary of tuples
    if isinstance(constraints, dict):
        constraints = (constraints, )

    cons = {'eq': (), 'ineq': ()}
    for ic, con in enumerate(constraints):
        # check type
        try:
            ctype = con['type'].lower()
        except KeyError:
            raise KeyError('Constraint %d has no type defined.' % ic)
        except TypeError:
            raise TypeError('Constraints must be defined using a '
                            'dictionary.')
        except AttributeError:
            raise TypeError("Constraint's type must be a string.")
        else:
            if ctype not in ['eq', 'ineq']:
                raise ValueError("Unknown constraint type '%s'." % con['type'])

        # check function
        if 'fun' not in con:
            raise ValueError('Constraint %d has no function defined.' % ic)

        # check Jacobian
        cjac = con.get('jac')
        if cjac is None:
            # approximate Jacobian function. The factory function is needed
            # to keep a reference to `fun`, see gh-4240.
            def cjac_factory(fun):
                def cjac(x, *args):
                    if jac in ['2-point', '3-point', 'cs']:
                        return approx_derivative(fun, x, method=jac, args=args,
                                                 rel_step=finite_diff_rel_step)
                    else:
                        return approx_derivative(fun, x, method='2-point',
                                                 abs_step=epsilon, args=args)

                return cjac
            cjac = cjac_factory(con['fun'])

        # update constraints' dictionary
        cons[ctype] += ({'fun': con['fun'],
                         'jac': cjac,
                         'args': con.get('args', ())}, )

    exit_modes = {-1: "Gradient evaluation required (g & a)",
                   0: "Optimization terminated successfully",
                   1: "Function evaluation required (f & c)",
                   2: "More equality constraints than independent variables",
                   3: "More than 3*n iterations in LSQ subproblem",
                   4: "Inequality constraints incompatible",
                   5: "Singular matrix E in LSQ subproblem",
                   6: "Singular matrix C in LSQ subproblem",
                   7: "Rank-deficient equality constraint subproblem HFTI",
                   8: "Positive directional derivative for linesearch",
                   9: "Iteration limit exceeded"}

    # Transform x0 into an array.
    x = asfarray(x0).flatten()

    # SLSQP is sent 'old-style' bounds, 'new-style' bounds are required by
    # ScalarFunction
    if bounds is None or len(bounds) == 0:
        new_bounds = (-np.inf, np.inf)
    else:
        new_bounds = old_bound_to_new(bounds)

    # clip the initial guess to bounds, otherwise ScalarFunction doesn't work
    x = np.clip(x, new_bounds[0], new_bounds[1])

    # Set the parameters that SLSQP will need
    # meq, mieq: number of equality and inequality constraints
    meq = sum(map(len, [atleast_1d(c['fun'](x, *c['args']))
              for c in cons['eq']]))
    mieq = sum(map(len, [atleast_1d(c['fun'](x, *c['args']))
               for c in cons['ineq']]))
    # m = The total number of constraints
    m = meq + mieq
    # la = The number of constraints, or 1 if there are no constraints
    la = array([1, m]).max()
    # n = The number of independent variables
    n = len(x)

    # Define the workspaces for SLSQP
    n1 = n + 1
    mineq = m - meq + n1 + n1
    len_w = (3*n1+m)*(n1+1)+(n1-meq+1)*(mineq+2) + 2*mineq+(n1+mineq)*(n1-meq) \
            + 2*meq + n1 + ((n+1)*n)//2 + 2*m + 3*n + 3*n1 + 1
    len_jw = mineq
    w = zeros(len_w)
    jw = zeros(len_jw)

    # Decompose bounds into xl and xu
    if bounds is None or len(bounds) == 0:
        xl = np.empty(n, dtype=float)
        xu = np.empty(n, dtype=float)
        xl.fill(np.nan)
        xu.fill(np.nan)
    else:
        bnds = array(bounds, float)
        if bnds.shape[0] != n:
            raise IndexError('SLSQP Error: the length of bounds is not '
                             'compatible with that of x0.')

        with np.errstate(invalid='ignore'):
            bnderr = bnds[:, 0] > bnds[:, 1]

        if bnderr.any():
            raise ValueError('SLSQP Error: lb > ub in bounds %s.' %
                             ', '.join(str(b) for b in bnderr))
        xl, xu = bnds[:, 0], bnds[:, 1]

        # Mark infinite bounds with nans; the Fortran code understands this
        infbnd = ~isfinite(bnds)
        xl[infbnd[:, 0]] = np.nan
        xu[infbnd[:, 1]] = np.nan

    # ScalarFunction provides function and gradient evaluation
    sf = _prepare_scalar_function(func, x, jac=jac, args=args, epsilon=eps,
                                  finite_diff_rel_step=finite_diff_rel_step,
                                  bounds=new_bounds)
    func = sf.fun
    fprime = sf.grad

    # Initialize the iteration counter and the mode value
    mode = array(0, int)
    acc = array(acc, float)
    majiter = array(iter, int)
    majiter_prev = 0

    # Initialize internal SLSQP state variables
    alpha = array(0, float)
    f0 = array(0, float)
    gs = array(0, float)
    h1 = array(0, float)
    h2 = array(0, float)
    h3 = array(0, float)
    h4 = array(0, float)
    t = array(0, float)
    t0 = array(0, float)
    tol = array(0, float)
    iexact = array(0, int)
    incons = array(0, int)
    ireset = array(0, int)
    itermx = array(0, int)
    line = array(0, int)
    n1 = array(0, int)
    n2 = array(0, int)
    n3 = array(0, int)

    # Print the header if iprint >= 2
    if iprint >= 2:
        print("%5s %5s %16s %16s" % ("NIT", "FC", "OBJFUN", "GNORM"))

    while 1:

        if mode == 0 or mode == 1:  # objective and constraint evaluation required

            # Compute objective function
            fx = func(x)
            try:
                fx = float(np.asarray(fx))
            except (TypeError, ValueError):
                raise ValueError("Objective function must return a scalar")
            # Compute the constraints
            if cons['eq']:
                c_eq = concatenate([atleast_1d(con['fun'](x, *con['args']))
                                    for con in cons['eq']])
            else:
                c_eq = zeros(0)
            if cons['ineq']:
                c_ieq = concatenate([atleast_1d(con['fun'](x, *con['args']))
                                     for con in cons['ineq']])
            else:
                c_ieq = zeros(0)

            # Now combine c_eq and c_ieq into a single matrix
            c = concatenate((c_eq, c_ieq))

        if mode == 0 or mode == -1:  # gradient evaluation required

            # Compute the derivatives of the objective function
            # For some reason SLSQP wants g dimensioned to n+1
            g = append(fprime(x), 0.0)

            # Compute the normals of the constraints
            if cons['eq']:
                a_eq = vstack([con['jac'](x, *con['args'])
                               for con in cons['eq']])
            else:  # no equality constraint
                a_eq = zeros((meq, n))

            if cons['ineq']:
                a_ieq = vstack([con['jac'](x, *con['args'])
                                for con in cons['ineq']])
            else:  # no inequality constraint
                a_ieq = zeros((mieq, n))

            # Now combine a_eq and a_ieq into a single a matrix
            if m == 0:  # no constraints
                a = zeros((la, n))
            else:
                a = vstack((a_eq, a_ieq))
            a = concatenate((a, zeros([la, 1])), 1)

        # Call SLSQP
        slsqp(m, meq, x, xl, xu, fx, c, g, a, acc, majiter, mode, w, jw,
              alpha, f0, gs, h1, h2, h3, h4, t, t0, tol,
              iexact, incons, ireset, itermx, line,
              n1, n2, n3)

        # call callback if major iteration has incremented
        if callback is not None and majiter > majiter_prev:
            callback(np.copy(x))

        # Print the status of the current iterate if iprint > 2 and the
        # major iteration has incremented
        if iprint >= 2 and majiter > majiter_prev:
            print("%5i %5i % 16.6E % 16.6E" % (majiter, sf.nfev,
                                               fx, linalg.norm(g)))

        # If exit mode is not -1 or 1, slsqp has completed
        if abs(mode) != 1:
            break

        majiter_prev = int(majiter)

    # Optimization loop complete. Print status if requested
    if iprint >= 1:
        print(exit_modes[int(mode)] + "    (Exit mode " + str(mode) + ')')
        print("            Current function value:", fx)
        print("            Iterations:", majiter)
        print("            Function evaluations:", sf.nfev)
        print("            Gradient evaluations:", sf.ngev)

    return OptimizeResult(x=x, fun=fx, jac=g[:-1], nit=int(majiter),
                          nfev=sf.nfev, njev=sf.ngev, status=int(mode),
                          message=exit_modes[int(mode)], success=(mode == 0))