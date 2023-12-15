    def execute(self, sql, parameters=()):
        """Same as :meth:`python:sqlite3.Connection.execute`."""
        if self.debug:
            tail = " with {!r}".format(parameters) if parameters else ""
            self.debug.write("Executing {!r}{}".format(sql, tail))
        try:
            try:
                return self.con.execute(sql, parameters)
            except Exception:
                # In some cases, an error might happen that isn't really an
                # error.  Try again immediately.
                # https://github.com/nedbat/coveragepy/issues/1010
                return self.con.execute(sql, parameters)
        except sqlite3.Error as exc:
            msg = str(exc)
            try:
                # `execute` is the first thing we do with the database, so try
                # hard to provide useful hints if something goes wrong now.
                with open(self.filename, "rb") as bad_file:
                    cov4_sig = b"!coverage.py: This is a private format"
                    if bad_file.read(len(cov4_sig)) == cov4_sig:
                        msg = (
                            "Looks like a coverage 4.x data file. "
                            "Are you mixing versions of coverage?"
                        )
            except Exception:
                pass
            if self.debug:
                self.debug.write("EXCEPTION from execute: {}".format(msg))
            raise CoverageException("Couldn't use data file {!r}: {}".format(self.filename, msg))