def main():
    # distutils depends on setup.py beeing executed from the same dir.
    # Most of our custom commands work either way, but this makes
    # it work in all cases.
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    const = exec_module(os.path.join("quodlibet", "const.py"))

    # convert to a setuptools compatible version string
    version = const.VERSION_TUPLE
    if version[-1] == -1:
        version_string = ".".join(map(str, version[:-1])) + ".dev0"
    else:
        version_string = ".".join(map(str, version))

    # find all packages
    package_path = "quodlibet"
    packages = []
    for root, dirnames, filenames in os.walk(package_path):
        if "__init__.py" in filenames:
            relpath = os.path.relpath(root, os.path.dirname(package_path))
            package_name = relpath.replace(os.sep, ".")
            packages.append(package_name)
    assert packages

    setup_kwargs = {
        'distclass': GDistribution,
        'name': "quodlibet",
        'version': version_string,
        'url': "https://quodlibet.readthedocs.org",
        'description': "a music library, tagger, and player",
        'author': "Joe Wreschnig, Michael Urman, & others",
        'author_email': "quod-libet-development@googlegroups.com",
        'maintainer': "Steven Robertson and Christoph Reiter",
        'license': "GNU GPL v2",
        'packages': packages,
        'package_data': {
            "quodlibet": [
                "images/hicolor/*/*/*.png",
                "images/hicolor/*/*/*.svg",
            ],
        },
        'scripts': ["quodlibet.py", "exfalso.py", "operon.py"],
        'po_directory': "po",
        'po_package': "quodlibet",
        'shortcuts': ["data/quodlibet.desktop", "data/exfalso.desktop"],
        'dbus_services': [
            "data/net.sacredchao.QuodLibet.service",
            # https://github.com/quodlibet/quodlibet/issues/1268
            # "data/org.mpris.MediaPlayer2.quodlibet.service",
            # "data/org.mpris.quodlibet.service",
        ],
        'appdata': [
            "data/quodlibet.appdata.xml",
            "data/exfalso.appdata.xml",
        ],
        'man_pages': [
            "data/quodlibet.1",
            "data/exfalso.1",
            "data/operon.1",
        ],
        "search_provider": "data/quodlibet-search-provider.ini",
        "coverage_options": {
            "directory": "coverage",
        },
    }

    if os.name == 'nt':
        def recursive_include_py2exe(dir_, pre, ext):
            all_ = []
            dir_ = os.path.join(dir_, pre)
            for path, dirs, files in os.walk(dir_):
                all_path = []
                for file_ in files:
                    if file_.split('.')[-1] in ext:
                        all_path.append(os.path.join(path, file_))
                if all_path:
                    all_.append((path, all_path))
            return all_

        data_files = [('', ['COPYING'])] + recursive_include_py2exe(
            "quodlibet", "images", ("svg", "png"))

        import certifi
        data_files.append(("certifi", [certifi.where()]))

        # py2exe can only handle simple versions
        if setup_kwargs["version"].endswith(".dev0"):
            setup_kwargs["version"] = setup_kwargs["version"][:-5]

        CMD_SUFFIX = "-cmd"
        GUI_TOOLS = ["quodlibet", "exfalso"]

        for gui_name in GUI_TOOLS:
            setup_kwargs.setdefault("windows", []).append({
                "script": "%s.py" % gui_name,
                "icon_resources": [(1,
                   os.path.join('..', 'win_installer', 'misc',
                                '%s.ico' % gui_name))],
            })

            # add a cmd version that supports stdout but opens a console
            setup_kwargs.setdefault("console", []).append({
                "script": "%s%s.py" % (gui_name, CMD_SUFFIX),
                "icon_resources": [(1,
                   os.path.join('..', 'win_installer', 'misc',
                                '%s.ico' % gui_name))],
            })
            setup_kwargs["scripts"].append("%s%s.py" % (gui_name, CMD_SUFFIX))

        for cli_name in ["operon"]:
            setup_kwargs.setdefault("console", []).append({
                "script": "%s.py" % cli_name,
            })

        setup_kwargs.update({
            'data_files': data_files,
            'options': {
                'py2exe': {
                    'packages': ('encodings, feedparser, quodlibet, '
                                 'HTMLParser, cairo, musicbrainzngs, shelve, '
                                 'json, gi, bsddb, dbhash'),
                    'excludes': ['Tkconstants', 'Tkinter'],
                    'skip_archive': True,
                    'dist_dir': os.path.join('dist', 'bin'),
                }
            }
        })

        for name in GUI_TOOLS:
            shutil.copy("%s.py" % name, "%s%s.py" % (name, CMD_SUFFIX))
        try:
            setup(**setup_kwargs)
        finally:
            for name in GUI_TOOLS:
                os.unlink("%s%s.py" % (name, CMD_SUFFIX))
    else:
        setup(**setup_kwargs)