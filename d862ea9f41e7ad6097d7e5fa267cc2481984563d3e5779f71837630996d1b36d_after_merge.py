def staged_files_only(cmd_runner):
    """Clear any unstaged changes from the git working directory inside this
    context.

    Args:
        cmd_runner - PrefixedCommandRunner
    """
    # Determine if there are unstaged files
    retcode, diff_stdout, _ = cmd_runner.run(
        ['git', 'diff', '--ignore-submodules', '--binary', '--exit-code'],
        retcode=None,
    )
    if retcode and diff_stdout.strip():
        patch_filename = cmd_runner.path('patch{0}'.format(int(time.time())))
        logger.warning('Unstaged files detected.')
        logger.info(
            'Stashing unstaged files to {0}.'.format(patch_filename),
        )
        # Save the current unstaged changes as a patch
        with open(patch_filename, 'w') as patch_file:
            patch_file.write(diff_stdout)

        # Clear the working directory of unstaged changes
        cmd_runner.run(['git', 'checkout', '--', '.'])
        try:
            yield
        finally:
            # Try to apply the patch we saved
            try:
                cmd_runner.run(['git', 'apply', patch_filename])
            except CalledProcessError:
                logger.warning(
                    'Stashed changes conflicted with hook auto-fixes... '
                    'Rolling back fixes...'
                )
                # We failed to apply the patch, presumably due to fixes made
                # by hooks.
                # Roll back the changes made by hooks.
                cmd_runner.run(['git', 'checkout', '--', '.'])
                cmd_runner.run(['git', 'apply', patch_filename])
            logger.info('Restored changes from {0}.'.format(patch_filename))
    else:
        # There weren't any staged files so we don't need to do anything
        # special
        yield