    def run(*a, **kw):
        hub = parent_hub or Hub.current
        with hub:
            try:
                self = current_thread()
                return old_run_func(self, *a, **kw)
            except Exception:
                reraise(*_capture_exception())