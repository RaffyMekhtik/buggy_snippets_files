        def _dup(lib, opts, args):
            self.config.set_args(opts)
            fmt = self.config['format'].get()
            album = self.config['album'].get(bool)
            full = self.config['full'].get(bool)
            strict = self.config['strict'].get(bool)
            keys = self.config['keys'].get()
            checksum = self.config['checksum'].get()
            copy = self.config['copy'].get()
            move = self.config['move'].get()
            delete = self.config['delete'].get(bool)
            tag = self.config['tag'].get()

            if album:
                keys = ['mb_albumid']
                items = lib.albums(decargs(args))
            else:
                items = lib.items(decargs(args))

            if self.config['path']:
                fmt = '$path'

            # Default format string for count mode.
            if self.config['count'] and not fmt:
                if album:
                    fmt = '$albumartist - $album'
                else:
                    fmt = '$albumartist - $album - $title'
                fmt += ': {0}'

            if checksum:
                if not isinstance(checksum, basestring):
                    raise UserError(
                        'duplicates: "checksum" option must be a command'
                    )
                for i in items:
                    k, _ = self._checksum(i, checksum)
                keys = [k]

            for obj_id, obj_count, objs in self._duplicates(items,
                                                            keys=keys,
                                                            full=full,
                                                            strict=strict):
                if obj_id:  # Skip empty IDs.
                    for o in objs:
                        self._process_item(o, lib,
                                           copy=copy,
                                           move=move,
                                           delete=delete,
                                           tag=tag,
                                           fmt=fmt.format(obj_count))