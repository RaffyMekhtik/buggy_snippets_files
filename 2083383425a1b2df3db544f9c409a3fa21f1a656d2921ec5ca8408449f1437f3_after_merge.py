    def __init__(self, loop, services, host, timeout):
        """Initialize a new UnicastDnsSdClientProtocol."""
        self.message = create_request(services)
        self.host = host
        self.timeout = timeout
        self.loop = loop
        self.transport = None
        self.semaphore = asyncio.Semaphore(value=0, loop=loop)
        self.result = None
        self._task = None