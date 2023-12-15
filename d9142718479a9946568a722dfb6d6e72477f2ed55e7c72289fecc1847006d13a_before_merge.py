def get_disabled(root=None):
    """
    Return a list of all disabled services

    root
        Enable/disable/mask unit files in the specified root directory

    CLI Example:

    .. code-block:: bash

        salt '*' service.get_disabled
    """
    ret = set()
    # Get disabled systemd units. Can't use --state=disabled here because it's
    # not present until systemd 216.
    out = __salt__["cmd.run"](
        _systemctl_cmd("--full --no-legend --no-pager list-unit-files", root=root),
        python_shell=False,
        ignore_retcode=True,
    )
    for line in salt.utils.itertools.split(out, "\n"):
        try:
            fullname, unit_state = line.strip().split(None, 1)
        except ValueError:
            continue
        else:
            if unit_state != "disabled":
                continue
        try:
            unit_name, unit_type = fullname.rsplit(".", 1)
        except ValueError:
            continue
        if unit_type in VALID_UNIT_TYPES:
            ret.add(unit_name if unit_type == "service" else fullname)

    # Add in any sysvinit services that are disabled
    ret.update(set([x for x in _get_sysv_services(root) if not _sysv_enabled(x, root)]))
    return sorted(ret)