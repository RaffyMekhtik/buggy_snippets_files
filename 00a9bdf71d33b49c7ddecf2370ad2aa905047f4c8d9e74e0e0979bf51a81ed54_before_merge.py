    def solve(self, problem: QuadraticProgram) -> OptimizationResult:
        """Tries to solves the given problem using the grover optimizer.

        Runs the optimizer to try to solve the optimization problem. If the problem cannot be,
        converted to a QUBO, this optimizer raises an exception due to incompatibility.

        Args:
            problem: The problem to be solved.

        Returns:
            The result of the optimizer applied to the problem.

        Raises:
            AttributeError: If the quantum instance has not been set.
            QiskitOptimizationError: If the problem is incompatible with the optimizer.
        """
        if self.quantum_instance is None:
            raise AttributeError('The quantum instance or backend has not been set.')

        self._verify_compatibility(problem)

        # convert problem to QUBO
        problem_ = self._convert(problem, self._converters)
        problem_init = deepcopy(problem_)

        # convert to minimization problem
        sense = problem_.objective.sense
        if sense == problem_.objective.Sense.MAXIMIZE:
            problem_.objective.sense = problem_.objective.Sense.MINIMIZE
            problem_.objective.constant = -problem_.objective.constant
            for i, val in problem_.objective.linear.to_dict().items():
                problem_.objective.linear[i] = -val
            for (i, j), val in problem_.objective.quadratic.to_dict().items():
                problem_.objective.quadratic[i, j] = -val
        self._num_key_qubits = len(problem_.objective.linear.to_array())  # type: ignore

        # Variables for tracking the optimum.
        optimum_found = False
        optimum_key = math.inf
        optimum_value = math.inf
        threshold = 0
        n_key = len(problem_.variables)
        n_value = self._num_value_qubits

        # Variables for tracking the solutions encountered.
        num_solutions = 2 ** n_key
        keys_measured = []

        # Variables for result object.
        operation_count = {}
        iteration = 0

        # Variables for stopping if we've hit the rotation max.
        rotations = 0
        max_rotations = int(np.ceil(100 * np.pi / 4))

        # Initialize oracle helper object.
        qr_key_value = QuantumRegister(self._num_key_qubits + self._num_value_qubits)
        orig_constant = problem_.objective.constant
        measurement = not self.quantum_instance.is_statevector
        oracle, is_good_state = self._get_oracle(qr_key_value)

        while not optimum_found:
            m = 1
            improvement_found = False

            # Get oracle O and the state preparation operator A for the current threshold.
            problem_.objective.constant = orig_constant - threshold
            a_operator = self._get_a_operator(qr_key_value, problem_)

            # Iterate until we measure a negative.
            loops_with_no_improvement = 0
            while not improvement_found:
                # Determine the number of rotations.
                loops_with_no_improvement += 1
                rotation_count = int(np.ceil(aqua_globals.random.uniform(0, m - 1)))
                rotations += rotation_count

                # Apply Grover's Algorithm to find values below the threshold.
                if rotation_count > 0:
                    # TODO: Utilize Grover's incremental feature - requires changes to Grover.
                    grover = Grover(oracle,
                                    state_preparation=a_operator,
                                    good_state=is_good_state)
                    circuit = grover.construct_circuit(rotation_count, measurement=measurement)
                else:
                    circuit = a_operator

                # Get the next outcome.
                outcome = self._measure(circuit)
                k = int(outcome[0:n_key], 2)
                v = outcome[n_key:n_key + n_value]
                int_v = self._bin_to_int(v, n_value) + threshold
                v = self._twos_complement(int_v, n_value)
                logger.info('Outcome: %s', outcome)
                logger.info('Value: %s = %s', v, int_v)

                # If the value is an improvement, we update the iteration parameters (e.g. oracle).
                if int_v < optimum_value:
                    optimum_key = k
                    optimum_value = int_v
                    logger.info('Current Optimum Key: %s', optimum_key)
                    logger.info('Current Optimum Value: %s', optimum_value)
                    if v.startswith('1'):
                        improvement_found = True
                        threshold = optimum_value
                else:
                    # Using Durr and Hoyer method, increase m.
                    m = int(np.ceil(min(m * 8 / 7, 2 ** (n_key / 2))))
                    logger.info('No Improvement. M: %s', m)

                    # Check if we've already seen this value.
                    if k not in keys_measured:
                        keys_measured.append(k)

                    # Assume the optimal if any of the stop parameters are true.
                    if loops_with_no_improvement >= self._n_iterations or \
                            len(keys_measured) == num_solutions or rotations >= max_rotations:
                        improvement_found = True
                        optimum_found = True

                # Track the operation count.
                operations = circuit.count_ops()
                operation_count[iteration] = operations
                iteration += 1
                logger.info('Operation Count: %s\n', operations)

        # If the constant is 0 and we didn't find a negative, the answer is likely 0.
        if optimum_value >= 0 and orig_constant == 0:
            optimum_key = 0

        opt_x = np.array([1 if s == '1' else 0 for s in ('{0:%sb}' % n_key).format(optimum_key)])

        # Compute function value
        fval = problem_init.objective.evaluate(opt_x)
        result = OptimizationResult(x=opt_x, fval=fval, variables=problem_.variables,
                                    status=OptimizationResultStatus.SUCCESS)

        # cast binaries back to integers
        result = self._interpret(result, self._converters)

        return GroverOptimizationResult(x=result.x, fval=result.fval, variables=result.variables,
                                        operation_counts=operation_count, n_input_qubits=n_key,
                                        n_output_qubits=n_value, intermediate_fval=fval,
                                        threshold=threshold,
                                        status=self._get_feasibility_status(problem, result.x))