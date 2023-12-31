def get_config_path(args):
    """
    Locates the main configuration file by name in some searchpaths.
    """

    # if we're in devmode, use only the build source config folder
    if config.DEVMODE:
        return Directory(os.path.join(config.BUILD_SRC_DIR, "cfg")).root

    # else, mount the possible locations in an union
    # to overlay the global dir and the user dir.
    result = Union().root

    # mount the global config dir
    # we don't use xdg config_dirs because that would be /etc/xdg/openage
    # and nobody would ever look in there.
    global_configs = pathlib.Path(config.GLOBAL_CONFIG_DIR)
    if global_configs.is_dir():
        result.mount(WriteBlocker(Directory(global_configs).root).root)

    # then the per-user config dir (probably ~/.config/openage)
    home_cfg = default_dirs.get_dir("config_home") / "openage"
    result.mount(
        Directory(
            home_cfg,
            create_if_missing=True
        ).root
    )

    # the optional command line argument overrides it all
    if args.cfg_dir:
        result.mount(Directory(args.cfg_dir).root)

    return result