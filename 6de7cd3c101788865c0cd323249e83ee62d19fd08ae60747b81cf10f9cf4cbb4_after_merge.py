    async def _do_run(self) -> None:
        with child_process_logging(self._boot_info):
            endpoint_name = self.get_endpoint_name()
            event_bus_service = AsyncioEventBusService(
                self._boot_info.trinity_config,
                endpoint_name,
            )
            async with background_asyncio_service(event_bus_service) as eventbus_manager:
                event_bus = await event_bus_service.get_event_bus()
                loop_monitoring_task = create_task(
                    self._loop_monitoring_task(event_bus),
                    f'AsyncioIsolatedComponent/{self.name}/loop_monitoring_task')

                do_run_task = create_task(
                    self.do_run(event_bus),
                    f'AsyncioIsolatedComponent/{self.name}/do_run')
                eventbus_task = create_task(
                    eventbus_manager.wait_finished(),
                    f'AsyncioIsolatedComponent/{self.name}/eventbus/wait_finished')
                try:
                    max_wait_after_cancellation = 2
                    tasks = [do_run_task, eventbus_task, loop_monitoring_task]
                    if self._boot_info.profile:
                        with profiler(f'profile_{self.get_endpoint_name()}'):
                            try:
                                await wait_first(
                                    tasks,
                                    max_wait_after_cancellation,
                                )
                            except asyncio.TimeoutError:
                                self.logger.warning(
                                    "Timed out waiting for tasks to "
                                    "terminate after cancellation: %s",
                                    tasks
                                )

                    else:
                        # XXX: When open_in_process() injects a KeyboardInterrupt into us (via
                        # coro.throw()), we hang forever here, until open_in_process() times
                        # out and sends us a SIGTERM, at which point we exit without executing
                        # either the except or the finally blocks below.
                        # See https://github.com/ethereum/trinity/issues/1711 for more.
                        try:
                            await wait_first(
                                tasks,
                                max_wait_after_cancellation,
                            )
                        except asyncio.TimeoutError:
                            self.logger.warning(
                                "Timed out waiting for tasks to terminate after cancellation: %s",
                                tasks
                            )

                except KeyboardInterrupt:
                    self.logger.debug("%s: KeyboardInterrupt", self)
                    # Currently we never reach this code path, but when we fix the issue above
                    # it will be needed.
                    return
                finally:
                    # Once we start seeing this in the logs after a Ctrl-C, we'll likely have
                    # figured out the issue above.
                    self.logger.debug("%s: do_run() finished", self)