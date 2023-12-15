def _command_is_valid(cmd):
    cmd_abspath = os.path.abspath(os.path.expanduser(cmd))
    return cmd in builtins.__xonsh_commands_cache__ or \
        (os.path.isfile(cmd_abspath) and os.access(cmd_abspath, os.X_OK))