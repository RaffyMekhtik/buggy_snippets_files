    def __init__(self, port, session):
        self._logger = logging.getLogger(self.__class__.__name__)

        self.port = port
        self.session = session
        self.vod_fileindex = None
        self.vod_download = None
        self.vod_info = defaultdict(dict)  # A dictionary containing info about the requested VOD streams.

        for _ in xrange(10000):
            try:
                HTTPServer.__init__(self, ("127.0.0.1", self.port), VideoRequestHandler)
                self._logger.debug("Listening at %d", self.port)
                break
            except socket.error:
                self._logger.debug("Listening failed at %d", self.port)
                self.port += 1
                continue

        self.server_thread = None

        self.daemon_threads = True
        self.allow_reuse_address = True