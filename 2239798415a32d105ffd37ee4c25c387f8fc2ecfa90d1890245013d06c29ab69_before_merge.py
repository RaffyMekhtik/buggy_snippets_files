def status(name, sig=None):
    '''
    Return the status for a service, returns the PID or an empty string if the
    service is running or not, pass a signature to use to find the service via
    ps

    CLI Example:

    .. code-block:: bash

        salt '*' service.status <service name> [service signature]
    '''
    cmd = 'sc query "{0}"'.format(name)
    statuses = __salt__['cmd.run'](cmd).splitlines()
    for line in statuses:
        if 'RUNNING' in line:
            return True
        elif 'PENDING' in line:
            return True
    return False