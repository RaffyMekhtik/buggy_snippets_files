    def _check_host_config(self):
        if self.host_config is None:
            return
        host_len = 0
        try:
            host_len = len(self.hosts)
        except TypeError:
            # Generator
            return
        if host_len != len(self.host_config):
            raise ValueError(
                "Host config entries must match number of hosts if provided. "
                "Got %s host config entries from %s hosts" % (
                    len(self.host_config), host_len))