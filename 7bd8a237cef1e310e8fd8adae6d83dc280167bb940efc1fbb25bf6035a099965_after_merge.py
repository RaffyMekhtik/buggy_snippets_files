def _publish(tgt,
             fun,
             arg=None,
             expr_form='glob',
             returner='',
             timeout=None,
             form='clean',
             roster=None):
    '''
    Publish a command "from the minion out to other minions". In reality, the
    minion does not execute this function, it is executed by the master. Thus,
    no access control is enabled, as minions cannot initiate publishes
    themselves.

    Salt-ssh publishes will default to whichever roster was used for the
    initiating salt-ssh call, and can be overridden using the ``roster``
    argument

    Returners are not currently supported

    The arguments sent to the minion publish function are separated with
    commas. This means that for a minion executing a command with multiple
    args it will look like this::

        salt-ssh system.example.com publish.publish '*' user.add 'foo,1020,1020'

    CLI Example:

    .. code-block:: bash

        salt-ssh system.example.com publish.publish '*' cmd.run 'ls -la /tmp'
    '''
    if fun.startswith('publish.'):
        log.info('Cannot publish publish calls. Returning {}')
        return {}

    # TODO: implement returners? Do they make sense for salt-ssh calls?
    if returner:
        log.warning('Returners currently not supported in salt-ssh publish')

    # Make sure args have been processed
    if arg is None:
        arg = []
    elif not isinstance(arg, list):
        arg = [salt.utils.args.yamlify_arg(arg)]
    else:
        arg = [salt.utils.args.yamlify_arg(x) for x in arg]
    if len(arg) == 1 and arg[0] is None:
        arg = []

    # Set up opts for the SSH object
    opts = copy.deepcopy(__context__['master_opts'])
    minopts = copy.deepcopy(__opts__)
    opts.update(minopts)
    if roster:
        opts['roster'] = roster
    if timeout:
        opts['timeout'] = timeout
    opts['argv'] = [fun] + arg
    opts['selected_target_option'] = expr_form
    opts['tgt'] = tgt
    opts['arg'] = arg

    # Create the SSH object to handle the actual call
    ssh = salt.client.ssh.SSH(opts)

    # Run salt-ssh to get the minion returns
    rets = {}
    for ret in ssh.run_iter():
        rets.update(ret)

    if form == 'clean':
        cret = {}
        for host in rets:
            if 'return' in rets[host]:
                cret[host] = rets[host]['return']
            else:
                cret[host] = rets[host]
        return cret
    else:
        return rets