def rsh(driver_addresses, key, host_hash, command, env, local_rank, verbose,
        background=True, events=None):
    """
    Method to run a command remotely given a host hash, local rank and driver addresses.

    This method connects to the SparkDriverService running on the Spark driver,
    retrieves all information required to connect to the task with given local rank
    of that host hash and invoke the command there.

    The method returns immediately after launching the command if background is True (default).
    When background is set to False, this method waits for command termination and returns
    command's result. If there is an exception while waiting for the result (i.e. connection reset)
    it returns -1.

    :param driver_addresses: driver's addresses
    :param key: used for encryption of parameters passed across the hosts
    :param host_hash: host hash to connect to
    :param command: command and arguments to invoke
    :param env: environment to use
    :param local_rank: local rank on the host of task to run the command in
    :param verbose: verbosity level
    :param background: run command in background if True, returns command result otherwise
    :param events: events to abort the command, only if background is True
    """
    if ':' in host_hash:
        raise Exception('Illegal host hash provided. Are you using Open MPI 4.0.0+?')

    driver_client = driver_service.SparkDriverClient(driver_addresses, key, verbose=verbose)
    task_indices = driver_client.task_host_hash_indices(host_hash)
    task_index = task_indices[local_rank]
    task_addresses = driver_client.all_task_addresses(task_index)
    task_client = task_service.SparkTaskClient(task_index, task_addresses, key, verbose=verbose)
    task_client.run_command(command, env)

    if not background:
        stop = None
        events = events or []
        for event in events:
            stop = threading.Event()
            on_event(event, task_client.abort_command, stop=stop)

        try:
            return task_client.wait_for_command_exit_code()
        except:
            traceback.print_exc()
            return -1
        finally:
            if stop is not None:
                stop.set()