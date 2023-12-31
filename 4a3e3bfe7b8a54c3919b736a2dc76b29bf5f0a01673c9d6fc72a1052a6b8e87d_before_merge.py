def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='list', required=True),
            format=dict(type='str', default='gz', choices=['bz2', 'gz', 'tar', 'xz', 'zip']),
            dest=dict(type='path'),
            exclude_path=dict(type='list'),
            remove=dict(type='bool', default=False),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    params = module.params
    check_mode = module.check_mode
    paths = params['path']
    dest = params['dest']
    exclude_paths = params['exclude_path']
    remove = params['remove']

    expanded_paths = []
    expanded_exclude_paths = []
    format = params['format']
    globby = False
    changed = False
    state = 'absent'

    # Simple or archive file compression (inapplicable with 'zip' since it's always an archive)
    archive = False
    successes = []

    # Fail early
    if not HAS_LZMA and format == 'xz':
        module.fail_json(msg="lzma or backports.lzma is required when using xz format.")

    for path in paths:
        path = os.path.expanduser(os.path.expandvars(path))

        # Expand any glob characters. If found, add the expanded glob to the
        # list of expanded_paths, which might be empty.
        if ('*' in path or '?' in path):
            expanded_paths = expanded_paths + glob.glob(path)
            globby = True

        # If there are no glob characters the path is added to the expanded paths
        # whether the path exists or not
        else:
            expanded_paths.append(path)

    # Only attempt to expand the exclude paths if it exists
    if exclude_paths:
        for exclude_path in exclude_paths:
            exclude_path = os.path.expanduser(os.path.expandvars(exclude_path))

            # Expand any glob characters. If found, add the expanded glob to the
            # list of expanded_paths, which might be empty.
            if ('*' in exclude_path or '?' in exclude_path):
                expanded_exclude_paths = expanded_exclude_paths + glob.glob(exclude_path)

                # If there are no glob character the exclude path is added to the expanded
                # exclude paths whether the path exists or not.
            else:
                expanded_exclude_paths.append(exclude_path)

    if not expanded_paths:
        return module.fail_json(path=', '.join(paths), expanded_paths=', '.join(expanded_paths), msg='Error, no source paths were found')

    # If we actually matched multiple files or TRIED to, then
    # treat this as a multi-file archive
    archive = globby or os.path.isdir(expanded_paths[0]) or len(expanded_paths) > 1

    # Default created file name (for single-file archives) to
    # <file>.<format>
    if not dest and not archive:
        dest = '%s.%s' % (expanded_paths[0], format)

    # Force archives to specify 'dest'
    if archive and not dest:
        module.fail_json(dest=dest, path=', '.join(paths), msg='Error, must specify "dest" when archiving multiple files or trees')

    archive_paths = []
    missing = []
    arcroot = ''

    for path in expanded_paths:
        # Use the longest common directory name among all the files
        # as the archive root path
        if arcroot == '':
            arcroot = os.path.dirname(path) + os.sep
        else:
            for i in range(len(arcroot)):
                if path[i] != arcroot[i]:
                    break

            if i < len(arcroot):
                arcroot = os.path.dirname(arcroot[0:i + 1])

            arcroot += os.sep

        # Don't allow archives to be created anywhere within paths to be removed
        if remove and os.path.isdir(path) and dest.startswith(path):
            module.fail_json(path=', '.join(paths), msg='Error, created archive can not be contained in source paths when remove=True')

        if os.path.lexists(path) and path not in expanded_exclude_paths:
            archive_paths.append(path)
        else:
            missing.append(path)

    # No source files were found but the named archive exists: are we 'compress' or 'archive' now?
    if len(missing) == len(expanded_paths) and dest and os.path.exists(dest):
        # Just check the filename to know if it's an archive or simple compressed file
        if re.search(r'(\.tar|\.tar\.gz|\.tgz|\.tbz2|\.tar\.bz2|\.tar\.xz|\.zip)$', os.path.basename(dest), re.IGNORECASE):
            state = 'archive'
        else:
            state = 'compress'

    # Multiple files, or globbiness
    elif archive:
        if not archive_paths:
            # No source files were found, but the archive is there.
            if os.path.lexists(dest):
                state = 'archive'
        elif missing:
            # SOME source files were found, but not all of them
            state = 'incomplete'

        archive = None
        size = 0
        errors = []

        if os.path.lexists(dest):
            size = os.path.getsize(dest)

        if state != 'archive':
            if check_mode:
                changed = True

            else:
                try:
                    # Slightly more difficult (and less efficient!) compression using zipfile module
                    if format == 'zip':
                        arcfile = zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED, True)

                    # Easier compression using tarfile module
                    elif format == 'gz' or format == 'bz2':
                        arcfile = tarfile.open(dest, 'w|' + format)

                    # python3 tarfile module allows xz format but for python2 we have to create the tarfile
                    # in memory and then compress it with lzma.
                    elif format == 'xz':
                        arcfileIO = io.BytesIO()
                        arcfile = tarfile.open(fileobj=arcfileIO, mode='w')

                    # Or plain tar archiving
                    elif format == 'tar':
                        arcfile = tarfile.open(dest, 'w')

                    match_root = re.compile('^%s' % re.escape(arcroot))
                    for path in archive_paths:
                        if os.path.isdir(path):
                            # Recurse into directories
                            for dirpath, dirnames, filenames in os.walk(path, topdown=True):
                                if not dirpath.endswith(os.sep):
                                    dirpath += os.sep

                                for dirname in dirnames:
                                    fullpath = dirpath + dirname
                                    arcname = match_root.sub('', fullpath)

                                    try:
                                        if format == 'zip':
                                            arcfile.write(fullpath, arcname)
                                        else:
                                            arcfile.add(fullpath, arcname, recursive=False)

                                    except Exception as e:
                                        errors.append('%s: %s' % (fullpath, to_native(e)))

                                for filename in filenames:
                                    fullpath = dirpath + filename
                                    arcname = match_root.sub('', fullpath)

                                    if not filecmp.cmp(fullpath, dest):
                                        try:
                                            if format == 'zip':
                                                arcfile.write(fullpath, arcname)
                                            else:
                                                arcfile.add(fullpath, arcname, recursive=False)

                                            successes.append(fullpath)
                                        except Exception as e:
                                            errors.append('Adding %s: %s' % (path, to_native(e)))
                        else:
                            if format == 'zip':
                                arcfile.write(path, match_root.sub('', path))
                            else:
                                arcfile.add(path, match_root.sub('', path), recursive=False)

                            successes.append(path)

                except Exception as e:
                    module.fail_json(msg='Error when writing %s archive at %s: %s' % (format == 'zip' and 'zip' or ('tar.' + format), dest, to_native(e)),
                                     exception=format_exc())

                if arcfile:
                    arcfile.close()
                    state = 'archive'

                if format == 'xz':
                    with lzma.open(dest, 'wb') as f:
                        f.write(arcfileIO.getvalue())
                    arcfileIO.close()

                if errors:
                    module.fail_json(msg='Errors when writing archive at %s: %s' % (dest, '; '.join(errors)))

        if state in ['archive', 'incomplete'] and remove:
            for path in successes:
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    elif not check_mode:
                        os.remove(path)
                except OSError as e:
                    errors.append(path)

            if errors:
                module.fail_json(dest=dest, msg='Error deleting some source files: ' + str(e), files=errors)

        # Rudimentary check: If size changed then file changed. Not perfect, but easy.
        if not check_mode and os.path.getsize(dest) != size:
            changed = True

        if successes and state != 'incomplete':
            state = 'archive'

    # Simple, single-file compression
    else:
        path = expanded_paths[0]

        # No source or compressed file
        if not (os.path.exists(path) or os.path.lexists(dest)):
            state = 'absent'

        # if it already exists and the source file isn't there, consider this done
        elif not os.path.lexists(path) and os.path.lexists(dest):
            state = 'compress'

        else:
            if module.check_mode:
                if not os.path.exists(dest):
                    changed = True
            else:
                size = 0
                f_in = f_out = arcfile = None

                if os.path.lexists(dest):
                    size = os.path.getsize(dest)

                try:
                    if format == 'zip':
                        arcfile = zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED, True)
                        arcfile.write(path, path[len(arcroot):])
                        arcfile.close()
                        state = 'archive'  # because all zip files are archives

                    else:
                        f_in = open(path, 'rb')

                        if format == 'gz':
                            f_out = gzip.open(dest, 'wb')
                        elif format == 'bz2':
                            f_out = bz2.BZ2File(dest, 'wb')
                        elif format == 'xz':
                            f_out = lzma.LZMAFile(dest, 'wb')
                        else:
                            raise OSError("Invalid format")

                        shutil.copyfileobj(f_in, f_out)

                    successes.append(path)

                except OSError as e:
                    module.fail_json(path=path, dest=dest, msg='Unable to write to compressed file: %s' % to_native(e), exception=format_exc())

                if arcfile:
                    arcfile.close()
                if f_in:
                    f_in.close()
                if f_out:
                    f_out.close()

                # Rudimentary check: If size changed then file changed. Not perfect, but easy.
                if os.path.getsize(dest) != size:
                    changed = True

            state = 'compress'

        if remove and not check_mode:
            try:
                os.remove(path)

            except OSError as e:
                module.fail_json(path=path, msg='Unable to remove source file: %s' % to_native(e), exception=format_exc())

    params['path'] = dest
    file_args = module.load_file_common_arguments(params)

    if not check_mode:
        changed = module.set_fs_attributes_if_different(file_args, changed)

    module.exit_json(archived=successes,
                     dest=dest,
                     changed=changed,
                     state=state,
                     arcroot=arcroot,
                     missing=missing,
                     expanded_paths=expanded_paths,
                     expanded_exclude_paths=expanded_exclude_paths)