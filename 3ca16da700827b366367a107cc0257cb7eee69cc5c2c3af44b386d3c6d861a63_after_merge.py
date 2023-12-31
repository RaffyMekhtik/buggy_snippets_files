def get(key, default='', delimiter=':', merge=None, omit_opts=False,
        omit_pillar=False, omit_master=False, omit_grains=False):
    '''
    .. versionadded: 0.14.0

    Attempt to retrieve the named value from the minion config file, grains,
    pillar or the master config. If the named value is not available, return the
    value specified by ``default``. If not specified, the default is an empty
    string.

    Values can also be retrieved from nested dictionaries. Assume the below
    data structure:

    .. code-block:: python

        {'pkg': {'apache': 'httpd'}}

    To retrieve the value associated with the ``apache`` key, in the
    sub-dictionary corresponding to the ``pkg`` key, the following command can
    be used:

    .. code-block:: bash

        salt myminion config.get pkg:apache

    The ``:`` (colon) is used to represent a nested dictionary level.

    .. versionchanged:: 2015.5.0
        The ``delimiter`` argument was added, to allow delimiters other than
        ``:`` to be used.

    This function traverses these data stores in this order, returning the
    first match found:

    - Minion configuration
    - Minion's grains
    - Minion's pillar data
    - Master configuration (requires :conf_minion:`pillar_opts` to be set to
      ``True`` in Minion config file in order to work)

    This means that if there is a value that is going to be the same for the
    majority of minions, it can be configured in the Master config file, and
    then overridden using the grains, pillar, or Minion config file.

    Adding config options to the Master or Minion configuration file is easy:

    .. code-block:: yaml

        my-config-option: value
        cafe-menu:
          - egg and bacon
          - egg sausage and bacon
          - egg and spam
          - egg bacon and spam
          - egg bacon sausage and spam
          - spam bacon sausage and spam
          - spam egg spam spam bacon and spam
          - spam sausage spam spam bacon spam tomato and spam

    .. note::
        Minion configuration options built into Salt (like those defined
        :ref:`here <configuration-salt-minion>`) will *always* be defined in
        the Minion configuration and thus *cannot be overridden by grains or
        pillar data*. However, additional (user-defined) configuration options
        (as in the above example) will not be in the Minion configuration by
        default and thus can be overridden using grains/pillar data by leaving
        the option out of the minion config file.

    **Arguments**

    delimiter
        .. versionadded:: 2015.5.0

        Override the delimiter used to separate nested levels of a data
        structure.

    merge
        .. versionadded:: 2015.5.0

        If passed, this parameter will change the behavior of the function so
        that, instead of traversing each data store above in order and
        returning the first match, the data stores are first merged together
        and then searched. The pillar data is merged into the master config
        data, then the grains are merged, followed by the Minion config data.
        The resulting data structure is then searched for a match. This allows
        for configurations to be more flexible.

        .. note::

            The merging described above does not mean that grain data will end
            up in the Minion's pillar data, or pillar data will end up in the
            master config data, etc. The data is just combined for the purposes
            of searching an amalgam of the different data stores.

        The supported merge strategies are as follows:

        - **recurse** - If a key exists in both dictionaries, and the new value
          is not a dictionary, it is replaced. Otherwise, the sub-dictionaries
          are merged together into a single dictionary, recursively on down,
          following the same criteria. For example:

          .. code-block:: python

              >>> dict1 = {'foo': {'bar': 1, 'qux': True},
                           'hosts': ['a', 'b', 'c'],
                           'only_x': None}
              >>> dict2 = {'foo': {'baz': 2, 'qux': False},
                           'hosts': ['d', 'e', 'f'],
                           'only_y': None}
              >>> merged
              {'foo': {'bar': 1, 'baz': 2, 'qux': False},
               'hosts': ['d', 'e', 'f'],
               'only_dict1': None,
               'only_dict2': None}

        - **overwrite** - If a key exists in the top level of both
          dictionaries, the new value completely overwrites the old. For
          example:

          .. code-block:: python

              >>> dict1 = {'foo': {'bar': 1, 'qux': True},
                           'hosts': ['a', 'b', 'c'],
                           'only_x': None}
              >>> dict2 = {'foo': {'baz': 2, 'qux': False},
                           'hosts': ['d', 'e', 'f'],
                           'only_y': None}
              >>> merged
              {'foo': {'baz': 2, 'qux': False},
               'hosts': ['d', 'e', 'f'],
               'only_dict1': None,
               'only_dict2': None}

    CLI Example:

    .. code-block:: bash

        salt '*' config.get pkg:apache
        salt '*' config.get lxc.container_profile:centos merge=recurse
    '''
    if merge is None:
        if not omit_opts:
            ret = salt.utils.data.traverse_dict_and_list(
                __opts__,
                key,
                '_|-',
                delimiter=delimiter)
            if ret != '_|-':
                return sdb.sdb_get(ret, __opts__)

        if not omit_grains:
            ret = salt.utils.data.traverse_dict_and_list(
                __grains__,
                key,
                '_|-',
                delimiter)
            if ret != '_|-':
                return sdb.sdb_get(ret, __opts__)

        if not omit_pillar:
            ret = salt.utils.data.traverse_dict_and_list(
                __pillar__,
                key,
                '_|-',
                delimiter=delimiter)
            if ret != '_|-':
                return sdb.sdb_get(ret, __opts__)

        if not omit_master:
            ret = salt.utils.data.traverse_dict_and_list(
                __pillar__.get('master', {}),
                key,
                '_|-',
                delimiter=delimiter)
            if ret != '_|-':
                return sdb.sdb_get(ret, __opts__)

        ret = salt.utils.data.traverse_dict_and_list(
            DEFAULTS,
            key,
            '_|-',
            delimiter=delimiter)
        log.debug("key: %s, ret: %s", key, ret)
        if ret != '_|-':
            return sdb.sdb_get(ret, __opts__)
    else:
        if merge not in ('recurse', 'overwrite'):
            log.warning('Unsupported merge strategy \'%s\'. Falling back '
                        'to \'recurse\'.', merge)
            merge = 'recurse'

        merge_lists = salt.config.master_config('/etc/salt/master').get('pillar_merge_lists')

        data = copy.copy(DEFAULTS)
        data = salt.utils.dictupdate.merge(data, __pillar__.get('master', {}), strategy=merge, merge_lists=merge_lists)
        data = salt.utils.dictupdate.merge(data, __pillar__, strategy=merge, merge_lists=merge_lists)
        data = salt.utils.dictupdate.merge(data, __grains__, strategy=merge, merge_lists=merge_lists)
        data = salt.utils.dictupdate.merge(data, __opts__, strategy=merge, merge_lists=merge_lists)
        ret = salt.utils.data.traverse_dict_and_list(
            data,
            key,
            '_|-',
            delimiter=delimiter)
        if ret != '_|-':
            return sdb.sdb_get(ret, __opts__)

    return default