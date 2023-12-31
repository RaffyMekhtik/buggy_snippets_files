def setup_cors(app, origins):
    """Setup cors."""
    import aiohttp_cors

    cors = aiohttp_cors.setup(app, defaults={
        host: aiohttp_cors.ResourceOptions(
            allow_headers=ALLOWED_CORS_HEADERS,
            allow_methods='*',
        ) for host in origins
    })

    def allow_cors(route, methods):
        """Allow cors on a route."""
        cors.add(route, {
            '*': aiohttp_cors.ResourceOptions(
                allow_headers=ALLOWED_CORS_HEADERS,
                allow_methods=methods,
            )
        })

    app['allow_cors'] = allow_cors

    if not origins:
        return

    async def cors_startup(app):
        """Initialize cors when app starts up."""
        cors_added = set()

        for route in list(app.router.routes()):
            if hasattr(route, 'resource'):
                route = route.resource
            if route in cors_added:
                continue
            cors.add(route)
            cors_added.add(route)

    app.on_startup.append(cors_startup)