    def fit(self, X, y, **kwargs):
        """Return a fair classifier under specified fairness constraints.

        :param X: The feature matrix
        :type X: numpy.ndarray or pandas.DataFrame

        :param y: The label vector
        :type y: numpy.ndarray, pandas.DataFrame, pandas.Series, or list
        """
        _, y_train, sensitive_features = _validate_and_reformat_input(X, y, **kwargs)

        n = y_train.shape[0]

        logger.debug("...Exponentiated Gradient STARTING")

        B = 1 / self._eps
        lagrangian = _Lagrangian(X, sensitive_features, y_train, self._estimator,
                                 self._constraints, self._eps, B)

        theta = pd.Series(0, lagrangian.constraints.index)
        Qsum = pd.Series(dtype="float64")
        gaps_EG = []
        gaps = []
        Qs = []

        last_regret_checked = _REGRET_CHECK_START_T
        last_gap = np.PINF
        for t in range(0, self._T):
            logger.debug("...iter=%03d", t)

            # set lambdas for every constraint
            lambda_vec = B * np.exp(theta) / (1 + np.exp(theta).sum())
            self._lambda_vecs[t] = lambda_vec
            lambda_EG = self._lambda_vecs.mean(axis=1)

            # select classifier according to best_h method
            h, h_idx = lagrangian.best_h(lambda_vec)

            if t == 0:
                if self._nu is None:
                    self._nu = _ACCURACY_MUL * (h(X) - y_train).abs().std() / np.sqrt(n)
                eta_min = self._nu / (2 * B)
                eta = self._eta_mul / B
                logger.debug("...eps=%.3f, B=%.1f, nu=%.6f, T=%d, eta_min=%.6f",
                             self._eps, B, self._nu, self._T, eta_min)

            if h_idx not in Qsum.index:
                Qsum.at[h_idx] = 0.0
            Qsum[h_idx] += 1.0
            gamma = lagrangian.gammas[h_idx]
            Q_EG = Qsum / Qsum.sum()
            result_EG = lagrangian.eval_gap(Q_EG, lambda_EG, self._nu)
            gap_EG = result_EG.gap()
            gaps_EG.append(gap_EG)

            if t == 0 or not _RUN_LP_STEP:
                gap_LP = np.PINF
            else:
                # saddle point optimization over the convex hull of
                # classifiers returned so far
                Q_LP, self._lambda_vecs_LP[t], result_LP = lagrangian.solve_linprog(self._nu)
                gap_LP = result_LP.gap()

            # keep values from exponentiated gradient or linear programming
            if gap_EG < gap_LP:
                Qs.append(Q_EG)
                gaps.append(gap_EG)
            else:
                Qs.append(Q_LP)
                gaps.append(gap_LP)

            logger.debug("%seta=%.6f, L_low=%.3f, L=%.3f, L_high=%.3f, gap=%.6f, disp=%.3f, "
                         "err=%.3f, gap_LP=%.6f",
                         _INDENTATION, eta, result_EG.L_low, result_EG.L, result_EG.L_high,
                         gap_EG, result_EG.gamma.max(), result_EG.error, gap_LP)

            if (gaps[t] < self._nu) and (t >= _MIN_T):
                # solution found
                break

            # update regret
            if t >= last_regret_checked * _REGRET_CHECK_INCREASE_T:
                best_gap = min(gaps_EG)

                if best_gap > last_gap * _SHRINK_REGRET:
                    eta *= _SHRINK_ETA
                last_regret_checked = t
                last_gap = best_gap

            # update theta based on learning rate
            theta += eta * (gamma - self._eps)

        # retain relevant result data
        gaps_series = pd.Series(gaps)
        gaps_best = gaps_series[gaps_series <= gaps_series.min() + _PRECISION]
        self._best_t = gaps_best.index[-1]
        self._best_gap = gaps[self._best_t]
        self._weights = Qs[self._best_t]
        self._hs = lagrangian.hs
        for h_idx in self._hs.index:
            if h_idx not in self._weights.index:
                self._weights.at[h_idx] = 0.0

        self._last_t = len(Qs) - 1
        self._predictors = lagrangian.classifiers
        self._n_oracle_calls = lagrangian.n_oracle_calls
        self._oracle_execution_times = lagrangian.oracle_execution_times
        self._lambda_vecs_lagrangian = lagrangian.lambdas

        logger.debug("...eps=%.3f, B=%.1f, nu=%.6f, T=%d, eta_min=%.6f",
                     self._eps, B, self._nu, self._T, eta_min)
        logger.debug("...last_t=%d, best_t=%d, best_gap=%.6f, n_oracle_calls=%d, n_hs=%d",
                     self._last_t, self._best_t, self._best_gap, lagrangian.n_oracle_calls,
                     len(lagrangian.classifiers))