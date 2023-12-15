    def commands(self):
        def scrub_func(lib, opts, args):
            # This is a little bit hacky, but we set a global flag to
            # avoid autoscrubbing when we're also explicitly scrubbing.
            global scrubbing
            scrubbing = True

            # Walk through matching files and remove tags.
            for item in lib.items(ui.decargs(args)):
                self._log.info(u'scrubbing: {0}',
                               util.displayable_path(item.path))

                # Get album art if we need to restore it.
                if opts.write:
                    try:
                        mf = mediafile.MediaFile(util.syspath(item.path),
                                                 config['id3v23'].get(bool))
                    except IOError as exc:
                        self._log.error(u'could not open file to scrub: {0}',
                                        exc)
                    art = mf.art

                # Remove all tags.
                self._scrub(item.path)

                # Restore tags, if enabled.
                if opts.write:
                    self._log.debug(u'writing new tags after scrub')
                    item.try_write()
                    if art:
                        self._log.info(u'restoring art')
                        mf = mediafile.MediaFile(util.syspath(item.path))
                        mf.art = art
                        mf.save()

            scrubbing = False

        scrub_cmd = ui.Subcommand('scrub', help='clean audio tags')
        scrub_cmd.parser.add_option('-W', '--nowrite', dest='write',
                                    action='store_false', default=True,
                                    help='leave tags empty')
        scrub_cmd.func = scrub_func

        return [scrub_cmd]