def get_clean_env(extra=None):
    """
    Returns cleaned up environment for subprocess execution.
    """
    environ = {}
    if extra is not None:
        environ.update(extra)
    variables = ('HOME', 'PATH', 'LANG', 'LD_LIBRARY_PATH')
    for var in variables:
        if var in os.environ:
            environ[var] = os.environ[var]
    return environ