def prepare(request=None, registry=None):
    """ This function pushes data onto the Pyramid threadlocal stack
    (request and registry), making those objects 'current'.  It
    returns a dictionary useful for bootstrapping a Pyramid
    application in a scripting environment.

    ``request`` is passed to the :app:`Pyramid` application root
    factory to compute the root. If ``request`` is None, a default
    will be constructed using the registry's :term:`Request Factory`
    via the :meth:`pyramid.interfaces.IRequestFactory.blank` method.

    If ``registry`` is not supplied, the last registry loaded from
    :attr:`pyramid.config.global_registries` will be used. If you
    have loaded more than one :app:`Pyramid` application in the
    current process, you may not want to use the last registry
    loaded, thus you can search the ``global_registries`` and supply
    the appropriate one based on your own criteria.

    The function returns a dictionary composed of ``root``,
    ``closer``, ``registry``, ``request`` and ``root_factory``.  The
    ``root`` returned is the application's root resource object.  The
    ``closer`` returned is a callable (accepting no arguments) that
    should be called when your scripting application is finished
    using the root.  ``registry`` is the resolved registry object.
    ``request`` is the request object passed or the constructed request
    if no request is passed.  ``root_factory`` is the root factory used
    to construct the root.

    This function may be used as a context manager to call the ``closer``
    automatically:

    .. code-block:: python

       registry = config.registry
       with prepare(registry) as env:
           request = env['request']
           # ...

    .. versionchanged:: 1.8

       Added the ability to use the return value as a context manager.

    """
    if registry is None:
        registry = getattr(request, 'registry', global_registries.last)
    if registry is None:
        raise ConfigurationError('No valid Pyramid applications could be '
                                 'found, make sure one has been created '
                                 'before trying to activate it.')
    if request is None:
        request = _make_request('/', registry)
    # NB: even though _make_request might have already set registry on
    # request, we reset it in case someone has passed in their own
    # request.
    request.registry = registry
    ctx = RequestContext(request)
    ctx.begin()
    apply_request_extensions(request)
    def closer():
        ctx.end()
    root_factory = registry.queryUtility(IRootFactory,
                                         default=DefaultRootFactory)
    root = root_factory(request)
    if getattr(request, 'context', None) is None:
        request.context = root
    return AppEnvironment(
        root=root,
        closer=closer,
        registry=registry,
        request=request,
        root_factory=root_factory,
    )