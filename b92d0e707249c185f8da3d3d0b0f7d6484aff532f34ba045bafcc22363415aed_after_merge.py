    def remote_call(self, interrupt=False, blocking=False, callback=None,
                    comm_id=None, timeout=None, display_error=False):
        """Get a handler for remote calls."""
        return super(KernelComm, self).remote_call(
            interrupt=interrupt, blocking=blocking, callback=callback,
            comm_id=comm_id, timeout=timeout, display_error=display_error)