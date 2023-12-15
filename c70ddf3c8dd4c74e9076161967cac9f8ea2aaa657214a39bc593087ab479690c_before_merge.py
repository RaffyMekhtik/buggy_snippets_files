    def stop(self, exitcode: int = 1):
        try:
            self.shutdown()
        except BaseException:
            pass

        if self.__message_counter:
            self.logger.info("%s %d messages since last logging.",
                             self._message_processed_verb,
                             self.__message_counter)

        self.__disconnect_pipelines()

        if self.logger:
            self.logger.info("Bot stopped.")
            logging.shutdown()
        else:
            self.__log_buffer.append(('info', 'Bot stopped.'))
            self.__print_log_buffer()

        if not getattr(self.parameters, 'testing', False):
            del self
            exit(exitcode)