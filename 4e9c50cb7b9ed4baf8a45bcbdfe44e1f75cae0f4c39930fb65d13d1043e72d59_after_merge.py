def setup_cors(app, origins):
    """Setup cors."""
    import aiohttp_cors

    cors = aiohttp_cors.setup(app, defaults={
        host: aiohttp_cors.ResourceOptions(
            allow_headers=ALLOWED_CORS_HEADERS,
            allow_methods='*',
        ) for host in origins
    })

    cors_added = set()

    def _allow_cors(route, config=None):
        """Allow cors on a route."""
        if hasattr(route, 'resource'):
            path = route.resource
        else:
            path = route

        path = path.canonical

        if path in cors_added:
            return

        cors.add(route, config)
        cors_added.add(path)

    app['allow_cors'] = lambda route: _allow_cors(route, {
        '*': aiohttp_cors.ResourceOptions(
            allow_headers=ALLOWED_CORS_HEADERS,
            allow_methods='*',
        )
    })

    if not origins:
        return

    async def cors_startup(app):
        """Initialize cors when app starts up."""
        for route in list(app.router.routes()):
            _allow_cors(route)

    app.on_startup.append(cors_startup)