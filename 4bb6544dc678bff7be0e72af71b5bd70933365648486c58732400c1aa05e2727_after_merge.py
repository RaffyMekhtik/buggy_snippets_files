    def _handle_signals(self, signum, sigframe):  # pylint: disable=unused-argument
        # escalate signal to the process manager processes
        self.minion.stop(signum)
        super(ProxyMinion, self)._handle_signals(signum, sigframe)