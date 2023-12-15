    def sample(self, values=None, method=mean_motion):
        """Samples an orbit to some specified time values.

        .. versionadded:: 0.8.0

        Parameters
        ----------
        values : Multiple options
            Number of interval points (default to 100),
            True anomaly values,
            Time values.

        Returns
        -------
        (Time, CartesianRepresentation)
            A tuple containing Time and Position vector in each
            given value.

        Notes
        -----
        When specifying a number of points, the initial and final
        position is present twice inside the result (first and
        last row). This is more useful for plotting.

        Examples
        --------
        >>> from astropy import units as u
        >>> from poliastro.examples import iss
        >>> iss.sample()
        >>> iss.sample(10)
        >>> iss.sample([0, 180] * u.deg)
        >>> iss.sample([0, 10, 20] * u.minute)
        >>> iss.sample([iss.epoch + iss.period / 2])

        """
        if values is None:
            return self.sample(100, method)

        elif isinstance(values, int):
            if self.ecc < 1:
                # first sample eccentric anomaly, then transform into true anomaly
                # why sampling eccentric anomaly uniformly to minimize error in the apocenter, see
                # http://www.dtic.mil/dtic/tr/fulltext/u2/a605040.pdf
                E_values = np.linspace(0, 2 * np.pi, values) * u.rad
                nu_values = E_to_nu(E_values, self.ecc)
            else:
                # Select a sensible limiting value for non-closed orbits
                # This corresponds to r = 3p
                nu_limit = np.arccos(-(1 - 1 / 3.) / self.ecc)
                nu_values = np.linspace(-nu_limit, nu_limit, values)
                nu_values = np.insert(nu_values, 0, self.ecc)

            return self.sample(nu_values, method)

        elif hasattr(values, "unit") and values.unit in ('rad', 'deg'):
            values = self._generate_time_values(values)
        return (values, self._sample(values, method))