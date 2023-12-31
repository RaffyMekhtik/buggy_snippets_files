def symlink_or_copy(do_copy, src, dst, relative_symlinks_ok=False):
    """
    Try symlinking a target, and if that fails, fall back to copying.
    """
    if not src.exists():
        raise RuntimeError("source {} does not exists".format(src))
    if src == dst:
        raise RuntimeError("source {} is same as destination ".format(src))

    def norm(val):
        if IS_PYPY and six.PY3:
            return str(val).encode(sys.getfilesystemencoding())
        return six.ensure_text(str(val))

    if do_copy is False and HAS_SYMLINK is False:  # if no symlink, always use copy
        do_copy = True
    if not do_copy:
        try:
            if not dst.is_symlink():  # can't link to itself!
                if relative_symlinks_ok:
                    assert src.parent == dst.parent
                    os.symlink(norm(src.name), norm(dst))
                else:
                    os.symlink(norm(str(src)), norm(dst))
        except OSError as exception:
            logging.warning(
                "symlink failed %r, for %s to %s, will try copy",
                exception,
                six.ensure_text(str(src)),
                six.ensure_text(str(dst)),
            )
            do_copy = True
    if do_copy:
        copier = shutil.copy2 if src.is_file() else shutil.copytree
        copier(norm(src), norm(dst))
    logging.debug("%s %s to %s", "copy" if do_copy else "symlink", six.ensure_text(str(src)), six.ensure_text(str(dst)))