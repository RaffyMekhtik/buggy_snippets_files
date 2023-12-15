    def _launched_all_configs_for_current_stage(self, run_history: RunHistory) -> bool:
        """
        This procedure queries if the addition of currently finished configs
        and running configs are sufficient for the current stage.
        If more configs are needed, it will return False.
        Parameters
        ----------
        run_history : RunHistory
            stores all runs we ran so far

        Returns
        -------
            bool: Whether or not to launch more configurations/instances/seed pairs
        """
        # selecting instance-seed subset for this budget, depending on the kind of budget
        curr_budget = self.all_budgets[self.stage]
        if self.instance_as_budget:
            prev_budget = int(self.all_budgets[self.stage - 1]) if self.stage > 0 else 0
            curr_insts = self.inst_seed_pairs[int(prev_budget):int(curr_budget)]
        else:
            curr_insts = self.inst_seed_pairs

        # _count_running_instances_for_challenger will count the running instances
        # of the last challenger. It makes sense here, because we assume that if we
        # moved to a new challenger, all instances have been launched for a previous
        # challenger
        running_instances = self._count_running_instances_for_challenger(run_history)
        n_insts_remaining = len(curr_insts) - (self.curr_inst_idx + running_instances)

        # Check which of the current configs is running
        my_configs = [c for c, i, s in self.run_tracker]
        running_configs = set()
        for k, v in run_history.data.items():
            if v.status == StatusType.RUNNING:
                if run_history.ids_config[k.config_id] in my_configs:
                    running_configs.add(k.config_id)

        # The total number of runs for this stage account for finished configurations
        # (success + failed + do not advance) + the offset + running but not finished
        # configurations. Also we account for the instances not launched for the
        # currently running configuration
        num_chal_available = (
            len(self.success_challengers | self.fail_challengers | self.do_not_advance_challengers)
            + self.fail_chal_offset + len(running_configs)
        )
        if num_chal_available == self.n_configs_in_stage[self.stage] and n_insts_remaining <= 0:
            return True
        else:
            return False