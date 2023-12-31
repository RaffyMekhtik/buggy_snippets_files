def init(names, host=None, saltcloud_mode=False, quiet=False, **kwargs):
    '''
    Initialize a new container


    .. code-block:: bash

        salt-run lxc.init name host=minion_id [cpuset=cgroups_cpuset] \\
                [cpushare=cgroups_cpushare] [memory=cgroups_memory] \\
                [template=lxc_template_name] [clone=original name] \\
                [profile=lxc_profile] [network_proflile=network_profile] \\
                [nic=network_profile] [nic_opts=nic_opts] \\
                [start=(true|false)] [seed=(true|false)] \\
                [install=(true|false)] [config=minion_config] \\
                [snapshot=(true|false)]

    names
        Name of the containers, supports a single name or a comma delimited
        list of names.

    host
        Minion on which to initialize the container **(required)**

    path
        path to the container parent
        default: /var/lib/lxc (system default)

        .. versionadded:: 2015.8.0

    saltcloud_mode
        init the container with the saltcloud opts format instead
        See lxc.init_interface module documentation

    cpuset
        cgroups cpuset.

    cpushare
        cgroups cpu shares.

    memory
        cgroups memory limit, in MB

        .. versionchanged:: 2015.5.0
            If no value is passed, no limit is set. In earlier Salt versions,
            not passing this value causes a 1024MB memory limit to be set, and
            it was necessary to pass ``memory=0`` to set no limit.

    template
        Name of LXC template on which to base this container

    clone
        Clone this container from an existing container

    profile
        A LXC profile (defined in config or pillar).

    network_profile
        Network profile to use for the container

        .. versionadded:: 2015.5.2

    nic
        .. deprecated:: 2015.5.0
            Use ``network_profile`` instead

    nic_opts
        Extra options for network interfaces. E.g.:

        ``{"eth0": {"mac": "aa:bb:cc:dd:ee:ff", "ipv4": "10.1.1.1", "ipv6": "2001:db8::ff00:42:8329"}}``

    start
        Start the newly created container.

    seed
        Seed the container with the minion config and autosign its key.
        Default: true

    install
        If salt-minion is not already installed, install it. Default: true

    config
        Optional config parameters. By default, the id is set to
        the name of the container.
    '''
    path = kwargs.get('path', None)
    if quiet:
        log.warning("'quiet' argument is being deprecated."
                 ' Please migrate to --quiet')
    ret = {'comment': '', 'result': True}
    if host is None:
        # TODO: Support selection of host based on available memory/cpu/etc.
        ret['comment'] = 'A host must be provided'
        ret['result'] = False
        return ret
    if isinstance(names, six.string_types):
        names = names.split(',')
    if not isinstance(names, list):
        ret['comment'] = 'Container names are not formed as a list'
        ret['result'] = False
        return ret
    # check that the host is alive
    client = salt.client.get_local_client(__opts__['conf_file'])
    alive = False
    try:
        if client.cmd(host, 'test.ping', timeout=20).get(host, None):
            alive = True
    except (TypeError, KeyError):
        pass
    if not alive:
        ret['comment'] = 'Host {0} is not reachable'.format(host)
        ret['result'] = False
        return ret

    log.info('Searching for LXC Hosts')
    data = __salt__['lxc.list'](host, quiet=True, path=path)
    for host, containers in six.iteritems(data):
        for name in names:
            if name in sum(six.itervalues(containers), []):
                log.info('Container \'{0}\' already exists'
                         ' on host \'{1}\','
                         ' init can be a NO-OP'.format(
                             name, host))
    if host not in data:
        ret['comment'] = 'Host \'{0}\' was not found'.format(host)
        ret['result'] = False
        return ret

    kw = salt.utils.clean_kwargs(**kwargs)
    pub_key = kw.get('pub_key', None)
    priv_key = kw.get('priv_key', None)
    explicit_auth = pub_key and priv_key
    approve_key = kw.get('approve_key', True)
    seeds = {}
    seed_arg = kwargs.get('seed', True)
    if approve_key and not explicit_auth:
        skey = salt.key.Key(__opts__)
        all_minions = skey.all_keys().get('minions', [])
        for name in names:
            seed = seed_arg
            if name in all_minions:
                try:
                    if client.cmd(name, 'test.ping', timeout=20).get(name, None):
                        seed = False
                except (TypeError, KeyError):
                    pass
            seeds[name] = seed
            kv = salt.utils.virt.VirtKey(host, name, __opts__)
            if kv.authorize():
                log.info('Container key will be preauthorized')
            else:
                ret['comment'] = 'Container key preauthorization failed'
                ret['result'] = False
                return ret

    log.info('Creating container(s) \'{0}\''
             ' on host \'{1}\''.format(names, host))

    cmds = []
    for name in names:
        args = [name]
        kw = salt.utils.clean_kwargs(**kwargs)
        if saltcloud_mode:
            kw = copy.deepcopy(kw)
            kw['name'] = name
            saved_kwargs = kw
            kw = client.cmd(
                host, 'lxc.cloud_init_interface', args + [kw],
                expr_form='list', timeout=600).get(host, {})
            kw.update(saved_kwargs)
        name = kw.pop('name', name)
        # be sure not to seed an already seeded host
        kw['seed'] = seeds.get(name, seed_arg)
        if not kw['seed']:
            kw.pop('seed_cmd', '')
        cmds.append(
            (host,
             name,
             client.cmd_iter(host, 'lxc.init', args, kwarg=kw, timeout=600)))
    done = ret.setdefault('done', [])
    errors = ret.setdefault('errors', _OrderedDict())

    for ix, acmd in enumerate(cmds):
        hst, container_name, cmd = acmd
        containers = ret.setdefault(hst, [])
        herrs = errors.setdefault(hst, _OrderedDict())
        serrs = herrs.setdefault(container_name, [])
        sub_ret = next(cmd)
        error = None
        if isinstance(sub_ret, dict) and host in sub_ret:
            j_ret = sub_ret[hst]
            container = j_ret.get('ret', {})
            if container and isinstance(container, dict):
                if not container.get('result', False):
                    error = container
            else:
                error = 'Invalid return for {0}: {1} {2}'.format(
                    container_name, container, sub_ret)
        else:
            error = sub_ret
            if not error:
                error = 'unknown error (no return)'
        if error:
            ret['result'] = False
            serrs.append(error)
        else:
            container['container_name'] = name
            containers.append(container)
            done.append(container)

    # marking ping status as True only and only if we have at
    # least provisioned one container
    ret['ping_status'] = bool(len(done))

    # for all provisioned containers, last job is to verify
    # - the key status
    # - we can reach them
    for container in done:
        # explicitly check and update
        # the minion key/pair stored on the master
        container_name = container['container_name']
        key = os.path.join(__opts__['pki_dir'], 'minions', container_name)
        if explicit_auth:
            fcontent = ''
            if os.path.exists(key):
                with salt.utils.fopen(key) as fic:
                    fcontent = fic.read().strip()
            if pub_key.strip() != fcontent:
                with salt.utils.fopen(key, 'w') as fic:
                    fic.write(pub_key)
                    fic.flush()
        mid = j_ret.get('mid', None)
        if not mid:
            continue

        def testping(**kw):
            mid_ = kw['mid']
            ping = client.cmd(mid_, 'test.ping', timeout=20)
            time.sleep(1)
            if ping:
                return 'OK'
            raise Exception('Unresponsive {0}'.format(mid_))
        ping = salt.utils.cloud.wait_for_fun(testping, timeout=21, mid=mid)
        if ping != 'OK':
            ret['ping_status'] = False
            ret['result'] = False

    # if no lxc detected as touched (either inited or verified)
    # we result to False
    if not done:
        ret['result'] = False
    if not quiet:
        __jid_event__.fire_event({'message': ret}, 'progress')
    return ret