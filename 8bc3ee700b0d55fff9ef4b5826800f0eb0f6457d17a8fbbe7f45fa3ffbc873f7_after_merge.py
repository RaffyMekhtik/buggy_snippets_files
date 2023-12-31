def _get_user_dirs(xdg_config_dir):
    """Returns a dict of XDG dirs read from
    ``$XDG_CONFIG_HOME/user-dirs.dirs``.

    This is used at import time for most users of :mod:`mopidy`. By rolling our
    own implementation instead of using :meth:`glib.get_user_special_dir` we
    make it possible for many extensions to run their test suites, which are
    importing parts of :mod:`mopidy`, in a virtualenv with global site-packages
    disabled, and thus no :mod:`glib` available.
    """

    dirs_file = os.path.join(xdg_config_dir, b'user-dirs.dirs')

    if not os.path.exists(dirs_file):
        return {}

    with open(dirs_file, 'rb') as fh:
        data = fh.read()

    data = b'[XDG_USER_DIRS]\n' + data
    data = data.replace(b'$HOME', os.path.expanduser(b'~'))
    data = data.replace(b'"', b'')

    config = configparser.RawConfigParser()
    config.readfp(io.BytesIO(data))

    return {
        k.upper().decode('utf-8'): os.path.abspath(v)
        for k, v in config.items('XDG_USER_DIRS') if v is not None
    }