    def fit(self, data, *args, **kwds):
        """
        Return MLEs for shape (if applicable), location, and scale
        parameters from data.

        MLE stands for Maximum Likelihood Estimate.  Starting estimates for
        the fit are given by input arguments; for any arguments not provided
        with starting estimates, ``self._fitstart(data)`` is called to generate
        such.

        One can hold some parameters fixed to specific values by passing in
        keyword arguments ``f0``, ``f1``, ..., ``fn`` (for shape parameters)
        and ``floc`` and ``fscale`` (for location and scale parameters,
        respectively).

        Parameters
        ----------
        data : array_like
            Data to use in calculating the MLEs.
        args : floats, optional
            Starting value(s) for any shape-characterizing arguments (those not
            provided will be determined by a call to ``_fitstart(data)``).
            No default value.
        kwds : floats, optional
            Starting values for the location and scale parameters; no default.
            Special keyword arguments are recognized as holding certain
            parameters fixed:

            - f0...fn : hold respective shape parameters fixed.
              Alternatively, shape parameters to fix can be specified by name.
              For example, if ``self.shapes == "a, b"``, ``fa``and ``fix_a``
              are equivalent to ``f0``, and ``fb`` and ``fix_b`` are
              equivalent to ``f1``.

            - floc : hold location parameter fixed to specified value.

            - fscale : hold scale parameter fixed to specified value.

            - optimizer : The optimizer to use.  The optimizer must take ``func``,
              and starting position as the first two arguments,
              plus ``args`` (for extra arguments to pass to the
              function to be optimized) and ``disp=0`` to suppress
              output as keyword arguments.

        Returns
        -------
        mle_tuple : tuple of floats
            MLEs for any shape parameters (if applicable), followed by those
            for location and scale. For most random variables, shape statistics
            will be returned, but there are exceptions (e.g. ``norm``).

        Notes
        -----
        This fit is computed by maximizing a log-likelihood function, with
        penalty applied for samples outside of range of the distribution. The
        returned answer is not guaranteed to be the globally optimal MLE, it
        may only be locally optimal, or the optimization may fail altogether.
        If the data contain any of np.nan, np.inf, or -np.inf, the fit routine
        will throw a RuntimeError.

        Examples
        --------

        Generate some data to fit: draw random variates from the `beta`
        distribution

        >>> from scipy.stats import beta
        >>> a, b = 1., 2.
        >>> x = beta.rvs(a, b, size=1000)

        Now we can fit all four parameters (``a``, ``b``, ``loc`` and ``scale``):

        >>> a1, b1, loc1, scale1 = beta.fit(x)

        We can also use some prior knowledge about the dataset: let's keep
        ``loc`` and ``scale`` fixed:

        >>> a1, b1, loc1, scale1 = beta.fit(x, floc=0, fscale=1)
        >>> loc1, scale1
        (0, 1)

        We can also keep shape parameters fixed by using ``f``-keywords. To
        keep the zero-th shape parameter ``a`` equal 1, use ``f0=1`` or,
        equivalently, ``fa=1``:

        >>> a1, b1, loc1, scale1 = beta.fit(x, fa=1, floc=0, fscale=1)
        >>> a1
        1

        Not all distributions return estimates for the shape parameters.
        ``norm`` for example just returns estimates for location and scale:

        >>> from scipy.stats import norm
        >>> x = norm.rvs(a, b, size=1000, random_state=123)
        >>> loc1, scale1 = norm.fit(x)
        >>> loc1, scale1
        (0.92087172783841631, 2.0015750750324668)
        """
        Narg = len(args)
        if Narg > self.numargs:
            raise TypeError("Too many input arguments.")

        if not np.isfinite(data).all():
            raise RuntimeError("The data contains non-finite values.")

        start = [None]*2
        if (Narg < self.numargs) or not ('loc' in kwds and
                                         'scale' in kwds):
            # get distribution specific starting locations
            start = self._fitstart(data)
            args += start[Narg:-2]
        loc = kwds.pop('loc', start[-2])
        scale = kwds.pop('scale', start[-1])
        args += (loc, scale)
        x0, func, restore, args = self._reduce_func(args, kwds)

        optimizer = kwds.pop('optimizer', optimize.fmin)
        # convert string to function in scipy.optimize
        if not callable(optimizer) and isinstance(optimizer, string_types):
            if not optimizer.startswith('fmin_'):
                optimizer = "fmin_"+optimizer
            if optimizer == 'fmin_':
                optimizer = 'fmin'
            try:
                optimizer = getattr(optimize, optimizer)
            except AttributeError:
                raise ValueError("%s is not a valid optimizer" % optimizer)

        # by now kwds must be empty, since everybody took what they needed
        if kwds:
            raise TypeError("Unknown arguments: %s." % kwds)

        vals = optimizer(func, x0, args=(ravel(data),), disp=0)
        if restore is not None:
            vals = restore(args, vals)
        vals = tuple(vals)
        return vals