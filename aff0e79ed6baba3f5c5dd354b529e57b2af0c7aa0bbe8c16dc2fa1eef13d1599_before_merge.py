    def read(self):
        # Read in the crontab from the system
        self.lines = []
        if self.cron_file:
            # read the cronfile
            try:
                f = open(self.cron_file, 'r')
                self.existing = f.read()
                self.lines = self.existing.splitlines()
                f.close()
            except IOError:
                # cron file does not exist
                return
            except Exception:
                raise CronTabError("Unexpected error:", sys.exc_info()[0])
        else:
            # using safely quoted shell for now, but this really should be two non-shell calls instead.  FIXME
            (rc, out, err) = self.module.run_command(self._read_user_execute(), use_unsafe_shell=True)

            if rc != 0 and rc != 1:  # 1 can mean that there are no jobs.
                raise CronTabError("Unable to read crontab")

            self.existing = out

            lines = out.splitlines()
            count = 0
            for l in lines:
                if count > 2 or (not re.match(r'# DO NOT EDIT THIS FILE - edit the master and reinstall.', l) and
                                 not re.match(r'# \(/tmp/.*installed on.*\)', l) and
                                 not re.match(r'# \(.*version.*\)', l)):
                    self.lines.append(l)
                else:
                    pattern = re.escape(l) + '[\r\n]?'
                    self.existing = re.sub(pattern, '', self.existing, 1)
                count += 1