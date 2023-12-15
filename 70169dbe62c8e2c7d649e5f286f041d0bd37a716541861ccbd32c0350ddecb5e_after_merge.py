    def dummy_request(self, original_request=None, **meta):
        """
        Construct a HttpRequest object that is, as far as possible, representative of ones that would
        receive this page as a response. Used for previewing / moderation and any other place where we
        want to display a view of this page in the admin interface without going through the regular
        page routing logic.

        If you pass in a real request object as original_request, additional information (e.g. client IP, cookies)
        will be included in the dummy request.
        """
        url = self.full_url
        if url:
            url_info = urlparse(url)
            hostname = url_info.hostname
            path = url_info.path
            port = url_info.port or 80
            scheme = url_info.scheme
        else:
            # Cannot determine a URL to this page - cobble one together based on
            # whatever we find in ALLOWED_HOSTS
            try:
                hostname = settings.ALLOWED_HOSTS[0]
                if hostname == '*':
                    # '*' is a valid value to find in ALLOWED_HOSTS[0], but it's not a valid domain name.
                    # So we pretend it isn't there.
                    raise IndexError
            except IndexError:
                hostname = 'localhost'
            path = '/'
            port = 80
            scheme = 'http'

        dummy_values = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': path,
            'SERVER_NAME': hostname,
            'SERVER_PORT': port,
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'HTTP_HOST': hostname,
            'wsgi.version': (1, 0),
            'wsgi.input': StringIO(),
            'wsgi.errors': StringIO(),
            'wsgi.url_scheme': scheme,
            'wsgi.multithread': True,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False,
        }

        # Add important values from the original request object, if it was provided.
        HEADERS_FROM_ORIGINAL_REQUEST = [
            'REMOTE_ADDR', 'HTTP_X_FORWARDED_FOR', 'HTTP_COOKIE', 'HTTP_USER_AGENT',
            'wsgi.version', 'wsgi.multithread', 'wsgi.multiprocess', 'wsgi.run_once',
        ]
        if original_request:
            for header in HEADERS_FROM_ORIGINAL_REQUEST:
                if header in original_request.META:
                    dummy_values[header] = original_request.META[header]

        # Add additional custom metadata sent by the caller.
        dummy_values.update(**meta)

        request = WSGIRequest(dummy_values)

        # Apply middleware to the request
        # Note that Django makes sure only one of the middleware settings are
        # used in a project
        if hasattr(settings, 'MIDDLEWARE'):
            handler = BaseHandler()
            handler.load_middleware()
            handler._middleware_chain(request)
        elif hasattr(settings, 'MIDDLEWARE_CLASSES'):
            # Pre Django 1.10 style - see http://www.mellowmorning.com/2011/04/18/mock-django-request-for-testing/
            handler = BaseHandler()
            handler.load_middleware()
            # call each middleware in turn and throw away any responses that they might return
            for middleware_method in handler._request_middleware:
                middleware_method(request)

        return request