def info(name):
    '''
    Get information about a service on the system

    Args:
        name (str): The name of the service. This is not the display name. Use
            ``get_service_name`` to find the service name.

    Returns:
        dict: A dictionary containing information about the service.

    CLI Example:

    .. code-block:: bash

        salt '*' service.info spooler
    '''
    try:
        handle_scm = win32service.OpenSCManager(
            None, None, win32service.SC_MANAGER_CONNECT)
    except pywintypes.error as exc:
        raise CommandExecutionError(
            'Failed to connect to the SCM: {0}'.format(exc[2]))

    try:
        handle_svc = win32service.OpenService(
            handle_scm, name,
            win32service.SERVICE_ENUMERATE_DEPENDENTS |
            win32service.SERVICE_INTERROGATE |
            win32service.SERVICE_QUERY_CONFIG |
            win32service.SERVICE_QUERY_STATUS)
    except pywintypes.error as exc:
        raise CommandExecutionError(
            'Failed To Open {0}: {1}'.format(name, exc[2]))

    try:
        config_info = win32service.QueryServiceConfig(handle_svc)
        status_info = win32service.QueryServiceStatusEx(handle_svc)

        try:
            description = win32service.QueryServiceConfig2(
                handle_svc, win32service.SERVICE_CONFIG_DESCRIPTION)
        except pywintypes.error:
            description = 'Failed to get description'

        delayed_start = win32service.QueryServiceConfig2(
            handle_svc, win32service.SERVICE_CONFIG_DELAYED_AUTO_START_INFO)
    finally:
        win32service.CloseServiceHandle(handle_scm)
        win32service.CloseServiceHandle(handle_svc)

    ret = dict()
    try:
        sid = win32security.LookupAccountName(
            '', 'NT Service\\{0}'.format(name))[0]
        ret['sid'] = win32security.ConvertSidToStringSid(sid)
    except pywintypes.error:
        ret['sid'] = 'Failed to get SID'

    ret['BinaryPath'] = config_info[3]
    ret['LoadOrderGroup'] = config_info[4]
    ret['TagID'] = config_info[5]
    ret['Dependencies'] = config_info[6]
    ret['ServiceAccount'] = config_info[7]
    ret['DisplayName'] = config_info[8]
    ret['Description'] = description
    ret['Status_ServiceCode'] = status_info['ServiceSpecificExitCode']
    ret['Status_CheckPoint'] = status_info['CheckPoint']
    ret['Status_WaitHint'] = status_info['WaitHint']
    ret['StartTypeDelayed'] = delayed_start

    flags = list()
    for bit in SERVICE_TYPE:
        if isinstance(bit, int):
            if config_info[0] & bit:
                flags.append(SERVICE_TYPE[bit])

    ret['ServiceType'] = flags if flags else config_info[0]

    flags = list()
    for bit in SERVICE_CONTROLS:
        if status_info['ControlsAccepted'] & bit:
            flags.append(SERVICE_CONTROLS[bit])

    ret['ControlsAccepted'] = flags if flags else status_info['ControlsAccepted']

    try:
        ret['Status_ExitCode'] = SERVICE_ERRORS[status_info['Win32ExitCode']]
    except KeyError:
        ret['Status_ExitCode'] = status_info['Win32ExitCode']

    try:
        ret['StartType'] = SERVICE_START_TYPE[config_info[1]]
    except KeyError:
        ret['StartType'] = config_info[1]

    try:
        ret['ErrorControl'] = SERVICE_ERROR_CONTROL[config_info[2]]
    except KeyError:
        ret['ErrorControl'] = config_info[2]

    try:
        ret['Status'] = SERVICE_STATE[status_info['CurrentState']]
    except KeyError:
        ret['Status'] = status_info['CurrentState']

    return ret