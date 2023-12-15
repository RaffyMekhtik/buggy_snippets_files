def get(tgt, fun, expr_form='glob', roster='flat'):
    '''
    Get data from the mine based on the target, function and expr_form

    This will actually run the function on all targeted minions (like
    publish.publish), as salt-ssh clients can't update the mine themselves.

    We will look for mine_functions in the roster, pillar, and master config,
    in that order, looking for a match for the defined function

    Targets can be matched based on any standard matching system that can be
    matched on the defined roster (in salt-ssh) via these keywords::

    CLI Example:

    .. code-block:: bash

        salt-ssh '*' mine.get '*' network.interfaces
        salt-ssh '*' mine.get 'myminion' network.interfaces roster=flat
        salt-ssh '*' mine.get '192.168.5.0' network.ipaddrs roster=scan
    '''
    # Set up opts for the SSH object
    opts = copy.deepcopy(__opts__)
    if roster:
        opts['roster'] = roster
    opts['argv'] = [fun]
    opts['selected_target_option'] = expr_form
    opts['tgt'] = tgt
    opts['arg'] = []

    # Create the SSH object to handle the actual call
    ssh = salt.client.ssh.SSH(opts)

    # Run salt-ssh to get the minion returns
    rets = {}
    for ret in ssh.run_iter(mine=True):
        rets.update(ret)

    cret = {}
    for host in rets:
        if 'return' in rets[host]:
            cret[host] = rets[host]['return']
        else:
            cret[host] = rets[host]
    return cret