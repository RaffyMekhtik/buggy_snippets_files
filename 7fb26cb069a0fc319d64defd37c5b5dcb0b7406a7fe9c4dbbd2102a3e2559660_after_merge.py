def raw_cron(user):
    '''
    Return the contents of the user's crontab

    CLI Example:

    .. code-block:: bash

        salt '*' cron.raw_cron root
    '''
    if _check_instance_uid_match(user) or __grains__.get('os_family') in ('Solaris', 'AIX'):
        cmd = 'crontab -l'
        # Preserve line endings
        lines = sdecode(__salt__['cmd.run_stdout'](cmd,
                                           runas=user,
                                           rstrip=False,
                                           python_shell=False)).splitlines(True)
    else:
        cmd = 'crontab -u {0} -l'.format(user)
        # Preserve line endings
        lines = sdecode(__salt__['cmd.run_stdout'](cmd,
                                           rstrip=False,
                                           python_shell=False)).splitlines(True)

    if len(lines) != 0 and lines[0].startswith('# DO NOT EDIT THIS FILE - edit the master and reinstall.'):
        del lines[0:3]
    return ''.join(lines)