def copy_asset(source: str, destination: str, excluded: PathMatcher = lambda path: False,
               context: Dict = None, renderer: "BaseRenderer" = None) -> None:
    """Copy asset files to destination recursively.

    On copying, it expands the template variables if context argument is given and
    the asset is a template file.

    :param source: The path to source file or directory
    :param destination: The path to destination directory
    :param excluded: The matcher to determine the given path should be copied or not
    :param context: The template variables.  If not given, template files are simply copied
    :param renderer: The template engine.  If not given, SphinxRenderer is used by default
    """
    if not os.path.exists(source):
        return

    if renderer is None:
        from sphinx.util.template import SphinxRenderer
        renderer = SphinxRenderer()

    ensuredir(destination)
    if os.path.isfile(source):
        copy_asset_file(source, destination, context, renderer)
        return

    for root, dirs, files in os.walk(source, followlinks=True):
        reldir = relative_path(source, root)
        for dir in dirs[:]:
            if excluded(posixpath.join(reldir, dir)):
                dirs.remove(dir)
            else:
                ensuredir(posixpath.join(destination, reldir, dir))

        for filename in files:
            if not excluded(posixpath.join(reldir, filename)):
                copy_asset_file(posixpath.join(root, filename),
                                posixpath.join(destination, reldir),
                                context, renderer)