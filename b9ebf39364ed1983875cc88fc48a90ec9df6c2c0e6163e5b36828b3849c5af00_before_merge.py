    def log_result(self, logger: Logger) -> None:
        """Use the given logger object to log our state."""
        logger.check_dependencies(self.failed + self.still_failing + self.skipped)
        with logger:
            for key, monitor in self.monitors.items():
                if check_group_match(monitor.group, logger.groups):
                    logger.save_result2(key, monitor)
                else:
                    module_logger.debug(
                        "not logging for %s due to group mismatch (monitor in group %s, "
                        "logger has groups %s",
                        key,
                        monitor.group,
                        logger.groups,
                    )
            try:
                for host_monitors in self.remote_monitors.values():
                    for name, monitor in host_monitors.items():
                        if check_group_match(monitor.group, logger.groups):
                            logger.save_result2(name, monitor)
                        else:
                            module_logger.debug(
                                "not logging for %s due to group mismatch (monitor in group %s, "
                                "logger has groups %s",
                                name,
                                monitor.group,
                                logger.groups,
                            )
            except Exception:  # pragma: no cover
                module_logger.exception("exception while logging remote monitors")