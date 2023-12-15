    def stats(self, *args, **kwds):
        """
        Some statistics of the given discrete RV.

        Parameters
        ----------
        arg1, arg2, arg3,... : array_like
            The shape parameter(s) for the distribution (see docstring of the
            instance object for more information).
        loc : array_like, optional
            Location parameter (default=0).
        moments : string, optional
            Composed of letters ['mvsk'] defining which moments to compute:

              - 'm' = mean,
              - 'v' = variance,
              - 's' = (Fisher's) skew,
              - 'k' = (Fisher's) kurtosis.

            The default is'mv'.

        Returns
        -------
        stats : sequence
            of requested moments.

        """
        try:
            kwds["moments"] = kwds.pop("moment") # test suite is full of these; a feature?
        except KeyError:
            pass
        args, loc, _, moments = self._parse_args_stats(*args, **kwds)
        loc = asarray(loc)
        args = tuple(map(asarray,args))
        cond = self._argcheck(*args) & (loc == loc)

        signature = inspect.getargspec(get_method_function(self._stats))
        if (signature[2] is not None) or ('moments' in signature[0]):
            mu, mu2, g1, g2 = self._stats(*args,**{'moments':moments})
        else:
            mu, mu2, g1, g2 = self._stats(*args)
        if g1 is None:
            mu3 = None
        else:
            mu3 = g1 * np.power(mu2, 1.5)
        default = valarray(shape(cond), self.badvalue)
        output = []

        # Use only entries that are valid in calculation
        goodargs = argsreduce(cond, *(args+(loc,)))
        loc, goodargs = goodargs[-1], goodargs[:-1]

        if 'm' in moments:
            if mu is None:
                mu = self._munp(1.0,*goodargs)
            out0 = default.copy()
            place(out0,cond,mu+loc)
            output.append(out0)

        if 'v' in moments:
            if mu2 is None:
                mu2p = self._munp(2.0,*goodargs)
                if mu is None:
                    mu = self._munp(1.0,*goodargs)
                mu2 = mu2p - mu*mu
            out0 = default.copy()
            place(out0,cond,mu2)
            output.append(out0)

        if 's' in moments:
            if g1 is None:
                mu3p = self._munp(3.0,*goodargs)
                if mu is None:
                    mu = self._munp(1.0,*goodargs)
                if mu2 is None:
                    mu2p = self._munp(2.0,*goodargs)
                    mu2 = mu2p - mu*mu
                mu3 = mu3p - 3*mu*mu2 - mu**3
                g1 = mu3 / np.power(mu2, 1.5)
            out0 = default.copy()
            place(out0,cond,g1)
            output.append(out0)

        if 'k' in moments:
            if g2 is None:
                mu4p = self._munp(4.0,*goodargs)
                if mu is None:
                    mu = self._munp(1.0,*goodargs)
                if mu2 is None:
                    mu2p = self._munp(2.0,*goodargs)
                    mu2 = mu2p - mu*mu
                if mu3 is None:
                    mu3p = self._munp(3.0,*goodargs)
                    mu3 = mu3p - 3*mu*mu2 - mu**3
                mu4 = mu4p - 4*mu*mu3 - 6*mu*mu*mu2 - mu**4
                g2 = mu4 / mu2**2.0 - 3.0
            out0 = default.copy()
            place(out0,cond,g2)
            output.append(out0)

        if len(output) == 1:
            return output[0]
        else:
            return tuple(output)