def gen_thin(cachedir, extra_mods='', overwrite=False, so_mods=''):
    '''
    Generate the salt-thin tarball and print the location of the tarball
    Optional additional mods to include (e.g. mako) can be supplied as a comma
    delimited string.  Permits forcing an overwrite of the output file as well.

    CLI Example:

    .. code-block:: bash

        salt-run thin.generate
        salt-run thin.generate mako
        salt-run thin.generate mako,wempy 1
        salt-run thin.generate overwrite=1
    '''
    thindir = os.path.join(cachedir, 'thin')
    if not os.path.isdir(thindir):
        os.makedirs(thindir)
    thintar = os.path.join(thindir, 'thin.tgz')
    thinver = os.path.join(thindir, 'version')
    salt_call = os.path.join(thindir, 'salt-call')
    with open(salt_call, 'w+') as fp_:
        fp_.write(SALTCALL)
    if os.path.isfile(thintar):
        if overwrite or not os.path.isfile(thinver):
            os.remove(thintar)
        elif open(thinver).read() == salt.__version__:
            return thintar
    tops = [
            os.path.dirname(salt.__file__),
            os.path.dirname(jinja2.__file__),
            os.path.dirname(yaml.__file__),
            os.path.dirname(requests.__file__)
            ]
    if HAS_MSGPACK:
        tops.append(os.path.dirname(msgpack.__file__))

    if HAS_URLLIB3:
        tops.append(os.path.dirname(urllib3.__file__))

    if HAS_SIX:
        tops.append(six.__file__.replace('.pyc', '.py'))

    if HAS_CHARDET:
        tops.append(os.path.dirname(chardet.__file__))

    for mod in [m for m in extra_mods.split(',') if m]:
        if mod not in locals() and mod not in globals():
            try:
                locals()[mod] = __import__(mod)
                moddir, modname = os.path.split(locals()[mod].__file__)
                base, ext = os.path.splitext(modname)
                if base == '__init__':
                    tops.append(moddir)
                else:
                    tops.append(os.path.join(moddir, base + '.py'))
            except ImportError:
                # Not entirely sure this is the right thing, but the only
                # options seem to be 1) fail, 2) spew errors, or 3) pass.
                # Nothing else in here spits errors, and the markupsafe code
                # doesn't bail on import failure, so I followed that lead.
                # And of course, any other failure still S/T's.
                pass
    for mod in [m for m in so_mods.split(',') if m]:
        try:
            locals()[mod] = __import__(mod)
            tops.append(locals()[mod].__file__)
        except ImportError:
            pass   # As per comment above
    if HAS_MARKUPSAFE:
        tops.append(os.path.dirname(markupsafe.__file__))
    tfp = tarfile.open(thintar, 'w:gz', dereference=True)
    start_dir = os.getcwd()
    for top in tops:
        base = os.path.basename(top)
        os.chdir(os.path.dirname(top))
        if not os.path.isdir(top):
            # top is a single file module
            tfp.add(base)
            continue
        for root, dirs, files in os.walk(base):
            for name in files:
                if not name.endswith(('.pyc', '.pyo')):
                    tfp.add(os.path.join(root, name))
    os.chdir(thindir)
    tfp.add('salt-call')
    with open(thinver, 'w+') as fp_:
        fp_.write(salt.__version__)
    os.chdir(os.path.dirname(thinver))
    tfp.add('version')
    os.chdir(start_dir)
    tfp.close()
    return thintar