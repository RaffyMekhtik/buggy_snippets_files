def set_value(hive,
              key,
              vname=None,
              vdata=None,
              vtype='REG_SZ',
              use_32bit_registry=False,
              volatile=False):
    '''
    Sets a registry value entry or the default value for a key.

    :param str hive: The name of the hive. Can be one of the following

        - HKEY_LOCAL_MACHINE or HKLM
        - HKEY_CURRENT_USER or HKCU
        - HKEY_USER or HKU

    :param str key: The key (looks like a path) to the value name.

    :param str vname: The value name. These are the individual name/data pairs
        under the key. If not passed, the key (Default) value will be set.

    :param object vdata: The value data to be set.
        What the type of this parameter
        should be is determined by the value of the vtype
        parameter. The correspondence
        is as follows:

        .. glossary::

           REG_BINARY
               binary data (i.e. str in python version < 3 and bytes in version >=3)
           REG_DWORD
               int
           REG_EXPAND_SZ
               str
           REG_MULTI_SZ
               list of objects of type str
           REG_SZ
               str

    :param str vtype: The value type.
        The possible values of the vtype parameter are indicated
        above in the description of the vdata parameter.

    :param bool use_32bit_registry: Sets the 32bit portion of the registry on
       64bit installations. On 32bit machines this is ignored.

    :param bool volatile: When this parameter has a value of True, the registry key will be
       made volatile (i.e. it will not persist beyond a system reset or shutdown).
       This parameter only has an effect when a key is being created and at no
       other time.

    :return: Returns True if successful, False if not
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' reg.set_value HKEY_LOCAL_MACHINE 'SOFTWARE\\Salt' 'version' '2015.5.2'

    This function is strict about the type of vdata. For instance the
    the next example will fail because vtype has a value of REG_SZ and vdata
    has a type of int (as opposed to str as expected).

    CLI Example:

    .. code-block:: bash

        salt '*' reg.set_value HKEY_LOCAL_MACHINE 'SOFTWARE\\Salt' 'version' '2015.5.2' \\
        vtype=REG_SZ vdata=0

    However, this next example where vdata is properly quoted should succeed.

    CLI Example:

    .. code-block:: bash

        salt '*' reg.set_value HKEY_LOCAL_MACHINE 'SOFTWARE\\Salt' 'version' '2015.5.2' \\
        vtype=REG_SZ vdata="'0'"

    An example of using vtype REG_BINARY is as follows:

    CLI Example:

    .. code-block:: bash

        salt '*' reg.set_value HKEY_LOCAL_MACHINE 'SOFTWARE\\Salt' 'version' '2015.5.2' \\
        vtype=REG_BINARY vdata='!!binary d2hhdCdzIHRoZSBwb2ludA=='

    An example of using vtype REG_LIST is as follows:

    CLI Example:

    .. code-block:: bash

        salt '*' reg.set_value HKEY_LOCAL_MACHINE 'SOFTWARE\\Salt' 'version' '2015.5.2' \\
        vtype=REG_LIST vdata='[a,b,c]'
    '''

    if PY2:
        try:
            local_hive = _mbcs_to_unicode(hive)
            local_key = _mbcs_to_unicode(key)
            local_vname = _mbcs_to_unicode(vname)
            local_vtype = _mbcs_to_unicode(vtype)
            local_vdata = _mbcs_to_unicode_wrap(vdata, local_vtype)
        except TypeError as exc:  # pylint: disable=E0602
            log.error(exc, exc_info=True)
            return False
    else:
        local_hive = hive
        local_key = key
        local_vname = vname
        local_vdata = vdata
        local_vtype = vtype

    registry = Registry()
    hkey = registry.hkeys[local_hive]
    vtype_value = registry.vtype[local_vtype]
    access_mask = registry.registry_32[use_32bit_registry] | _winreg.KEY_ALL_ACCESS
    if volatile:
        create_options = registry.opttype['REG_OPTION_VOLATILE']
    else:
        create_options = registry.opttype['REG_OPTION_NON_VOLATILE']

    try:
        handle, _ = RegCreateKeyEx(hkey, local_key, access_mask,
                                   Options=create_options)
        RegSetValueEx(handle, local_vname, 0, vtype_value, local_vdata)
        RegFlushKey(handle)
        RegCloseKey(handle)
        broadcast_change()
        return True
    except (win32apiError, SystemError, ValueError, TypeError) as exc:  # pylint: disable=E0602
        log.error(exc, exc_info=True)
        return False