    def run(self, iterator, play_context):
        '''
        The linear strategy is simple - get the next task and queue
        it for all hosts, then wait for the queue to drain before
        moving on to the next task
        '''

        # iteratate over each task, while there is one left to run
        result = self._tqm.RUN_OK
        work_to_do = True
        while work_to_do and not self._tqm._terminated:

            try:
                display.debug("getting the remaining hosts for this loop")
                hosts_left = [host for host in self._inventory.get_hosts(iterator._play.hosts) if host.name not in self._tqm._unreachable_hosts]
                display.debug("done getting the remaining hosts for this loop")

                # queue up this task for each host in the inventory
                callback_sent = False
                work_to_do = False

                host_results = []
                host_tasks = self._get_next_task_lockstep(hosts_left, iterator)

                # skip control
                skip_rest   = False
                choose_step = True

                # flag set if task is set to any_errors_fatal
                any_errors_fatal = False

                results = []
                for (host, task) in host_tasks:
                    if not task:
                        continue

                    if self._tqm._terminated:
                        break

                    run_once = False
                    work_to_do = True

                    # test to see if the task across all hosts points to an action plugin which
                    # sets BYPASS_HOST_LOOP to true, or if it has run_once enabled. If so, we
                    # will only send this task to the first host in the list.

                    try:
                        action = action_loader.get(task.action, class_only=True)
                    except KeyError:
                        # we don't care here, because the action may simply not have a
                        # corresponding action plugin
                        action = None

                    # check to see if this task should be skipped, due to it being a member of a
                    # role which has already run (and whether that role allows duplicate execution)
                    if task._role and task._role.has_run(host):
                        # If there is no metadata, the default behavior is to not allow duplicates,
                        # if there is metadata, check to see if the allow_duplicates flag was set to true
                        if task._role._metadata is None or task._role._metadata and not task._role._metadata.allow_duplicates:
                            display.debug("'%s' skipped because role has already run" % task)
                            continue

                    if task.action == 'meta':
                        # for the linear strategy, we run meta tasks just once and for
                        # all hosts currently being iterated over rather than one host
                        results.extend(self._execute_meta(task, play_context, iterator, host))
                        if task.args.get('_raw_params', None) != 'noop':
                            run_once = True
                    else:
                        # handle step if needed, skip meta actions as they are used internally
                        if self._step and choose_step:
                            if self._take_step(task):
                                choose_step = False
                            else:
                                skip_rest = True
                                break

                        display.debug("getting variables")
                        task_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, host=host, task=task)
                        self.add_tqm_variables(task_vars, play=iterator._play)
                        templar = Templar(loader=self._loader, variables=task_vars)
                        display.debug("done getting variables")

                        run_once = templar.template(task.run_once) or action and getattr(action, 'BYPASS_HOST_LOOP', False)

                        if (task.any_errors_fatal or run_once) and not task.ignore_errors:
                            any_errors_fatal = True

                        if not callback_sent:
                            display.debug("sending task start callback, copying the task so we can template it temporarily")
                            saved_name = task.name
                            display.debug("done copying, going to template now")
                            try:
                                task.name = to_text(templar.template(task.name, fail_on_undefined=False), nonstring='empty')
                                display.debug("done templating")
                            except:
                                # just ignore any errors during task name templating,
                                # we don't care if it just shows the raw name
                                display.debug("templating failed for some reason")
                                pass
                            display.debug("here goes the callback...")
                            self._tqm.send_callback('v2_playbook_on_task_start', task, is_conditional=False)
                            task.name = saved_name
                            callback_sent = True
                            display.debug("sending task start callback")

                        self._blocked_hosts[host.get_name()] = True
                        self._queue_task(host, task, task_vars, play_context)
                        del task_vars

                    # if we're bypassing the host loop, break out now
                    if run_once:
                        break

                    results += self._process_pending_results(iterator, max_passes=max(1, int(len(self._tqm._workers) * 0.1)))

                # go to next host/task group
                if skip_rest:
                    continue

                display.debug("done queuing things up, now waiting for results queue to drain")
                if self._pending_results > 0:
                    results += self._wait_on_pending_results(iterator)
                host_results.extend(results)

                all_role_blocks = []
                for hr in results:
                    # handle include_role
                    if hr._task.action == 'include_role':
                        loop_var = None
                        if hr._task.loop:
                            loop_var = 'item'
                            if hr._task.loop_control:
                                loop_var = hr._task.loop_control.loop_var or 'item'
                            include_results = hr._result.get('results', [])
                        else:
                            include_results = [ hr._result ]

                        for include_result in include_results:
                            if 'skipped' in include_result and include_result['skipped'] or 'failed' in include_result and include_result['failed']:
                                continue

                            display.debug("generating all_blocks data for role")
                            new_ir = hr._task.copy()
                            new_ir.vars.update(include_result.get('include_variables', dict()))
                            if loop_var and loop_var in include_result:
                                new_ir.vars[loop_var] = include_result[loop_var]

                            all_role_blocks.extend(new_ir.get_block_list(play=iterator._play, variable_manager=self._variable_manager, loader=self._loader))

                if len(all_role_blocks) > 0:
                    for host in hosts_left:
                        iterator.add_tasks(host, all_role_blocks)

                try:
                    included_files = IncludedFile.process_include_results(
                        host_results,
                        self._tqm,
                        iterator=iterator,
                        inventory=self._inventory,
                        loader=self._loader,
                        variable_manager=self._variable_manager
                    )
                except AnsibleError as e:
                    # this is a fatal error, so we abort here regardless of block state
                    return self._tqm.RUN_ERROR

                include_failure = False
                if len(included_files) > 0:
                    display.debug("we have included files to process")
                    noop_task = Task()
                    noop_task.action = 'meta'
                    noop_task.args['_raw_params'] = 'noop'
                    noop_task.set_loader(iterator._play._loader)

                    display.debug("generating all_blocks data")
                    all_blocks = dict((host, []) for host in hosts_left)
                    display.debug("done generating all_blocks data")
                    for included_file in included_files:
                        display.debug("processing included file: %s" % included_file._filename)
                        # included hosts get the task list while those excluded get an equal-length
                        # list of noop tasks, to make sure that they continue running in lock-step
                        try:
                            new_blocks = self._load_included_file(included_file, iterator=iterator)

                            display.debug("iterating over new_blocks loaded from include file")
                            for new_block in new_blocks:
                                task_vars = self._variable_manager.get_vars(
                                    loader=self._loader,
                                    play=iterator._play,
                                    task=included_file._task,
                                )
                                display.debug("filtering new block on tags")
                                final_block = new_block.filter_tagged_tasks(play_context, task_vars)
                                display.debug("done filtering new block on tags")

                                noop_block = Block(parent_block=task._parent)
                                noop_block.block  = [noop_task for t in new_block.block]
                                noop_block.always = [noop_task for t in new_block.always]
                                noop_block.rescue = [noop_task for t in new_block.rescue]

                                for host in hosts_left:
                                    if host in included_file._hosts:
                                        all_blocks[host].append(final_block)
                                    else:
                                        all_blocks[host].append(noop_block)
                            display.debug("done iterating over new_blocks loaded from include file")

                        except AnsibleError as e:
                            for host in included_file._hosts:
                                self._tqm._failed_hosts[host.name] = True
                                iterator.mark_host_failed(host)
                            display.error(to_text(e), wrap_text=False)
                            include_failure = True
                            continue

                    # finally go through all of the hosts and append the
                    # accumulated blocks to their list of tasks
                    display.debug("extending task lists for all hosts with included blocks")

                    for host in hosts_left:
                        iterator.add_tasks(host, all_blocks[host])

                    display.debug("done extending task lists")
                    display.debug("done processing included files")

                display.debug("results queue empty")

                display.debug("checking for any_errors_fatal")
                failed_hosts = []
                unreachable_hosts = []
                for res in results:
                    if res.is_failed() and iterator.is_failed(res._host):
                        failed_hosts.append(res._host.name)
                    elif res.is_unreachable():
                        unreachable_hosts.append(res._host.name)

                # if any_errors_fatal and we had an error, mark all hosts as failed
                if any_errors_fatal and (len(failed_hosts) > 0 or len(unreachable_hosts) > 0):
                    for host in hosts_left:
                        (s, _) = iterator.get_next_task_for_host(host, peek=True)
                        if s.run_state != iterator.ITERATING_RESCUE or \
                           s.run_state == iterator.ITERATING_RESCUE and s.fail_state & iterator.FAILED_RESCUE != 0:
                            self._tqm._failed_hosts[host.name] = True
                            result |= self._tqm.RUN_FAILED_BREAK_PLAY
                display.debug("done checking for any_errors_fatal")

                display.debug("checking for max_fail_percentage")
                if iterator._play.max_fail_percentage is not None and len(results) > 0:
                    percentage = iterator._play.max_fail_percentage / 100.0

                    if (len(self._tqm._failed_hosts) / len(results)) > percentage:
                        for host in hosts_left:
                            # don't double-mark hosts, or the iterator will potentially
                            # fail them out of the rescue/always states
                            if host.name not in failed_hosts:
                                self._tqm._failed_hosts[host.name] = True
                                iterator.mark_host_failed(host)
                        self._tqm.send_callback('v2_playbook_on_no_hosts_remaining')
                        result |= self._tqm.RUN_FAILED_BREAK_PLAY
                display.debug("done checking for max_fail_percentage")

                display.debug("checking to see if all hosts have failed and the running result is not ok")
                if result != self._tqm.RUN_OK and len(self._tqm._failed_hosts) >= len(hosts_left):
                    display.debug("^ not ok, so returning result now")
                    self._tqm.send_callback('v2_playbook_on_no_hosts_remaining')
                    return result
                display.debug("done checking to see if all hosts have failed")

            except (IOError, EOFError) as e:
                display.debug("got IOError/EOFError in task loop: %s" % e)
                # most likely an abort, return failed
                return self._tqm.RUN_UNKNOWN_ERROR

        # run the base class run() method, which executes the cleanup function
        # and runs any outstanding handlers which have been triggered

        return super(StrategyModule, self).run(iterator, play_context, result)