def query(url,
          method='GET',
          params=None,
          data=None,
          data_file=None,
          header_dict=None,
          header_list=None,
          header_file=None,
          username=None,
          password=None,
          auth=None,
          decode=False,
          decode_type='auto',
          status=False,
          headers=False,
          text=False,
          cookies=None,
          cookie_jar=None,
          cookie_format='lwp',
          persist_session=False,
          session_cookie_jar=None,
          data_render=False,
          data_renderer=None,
          header_render=False,
          header_renderer=None,
          template_dict=None,
          test=False,
          test_url=None,
          node='minion',
          port=80,
          opts=None,
          backend='tornado',
          requests_lib=None,
          ca_bundle=None,
          verify_ssl=None,
          cert=None,
          text_out=None,
          headers_out=None,
          decode_out=None,
          stream=False,
          streaming_callback=None,
          handle=False,
          agent=USERAGENT,
          hide_fields=None,
          **kwargs):
    '''
    Query a resource, and decode the return data
    '''
    ret = {}

    if opts is None:
        if node == 'master':
            opts = salt.config.master_config(
                os.path.join(syspaths.CONFIG_DIR, 'master')
            )
        elif node == 'minion':
            opts = salt.config.minion_config(
                os.path.join(syspaths.CONFIG_DIR, 'minion')
            )
        else:
            opts = {}

    if requests_lib is None:
        requests_lib = opts.get('requests_lib', False)

    if requests_lib is True:
        log.warn('Please set "backend" to "requests" instead of setting '
                 '"requests_lib" to "True"')

        if HAS_REQUESTS is False:
            ret['error'] = ('http.query has been set to use requests, but the '
                            'requests library does not seem to be installed')
            log.error(ret['error'])
            return ret

        backend = 'requests'

    else:
        requests_log = logging.getLogger('requests')
        requests_log.setLevel(logging.WARNING)

    # Some libraries don't support separation of url and GET parameters
    # Don't need a try/except block, since Salt depends on tornado
    url_full = tornado.httputil.url_concat(url, params)

    if ca_bundle is None:
        ca_bundle = get_ca_bundle(opts)

    if verify_ssl is None:
        verify_ssl = opts.get('verify_ssl', True)

    if cert is None:
        cert = opts.get('cert', None)

    if data_file is not None:
        data = _render(
            data_file, data_render, data_renderer, template_dict, opts
        )

    # Make sure no secret fields show up in logs
    log_url = sanitize_url(url_full, hide_fields)

    log.debug('Requesting URL {0} using {1} method'.format(log_url, method))
    if method == 'POST':
        # Make sure no secret fields show up in logs
        if isinstance(data, dict):
            log_data = data.copy()
            if isinstance(hide_fields, list):
                for item in data:
                    for field in hide_fields:
                        if item == field:
                            log_data[item] = 'XXXXXXXXXX'
            log.trace('Request POST Data: {0}'.format(pprint.pformat(log_data)))
        else:
            log.trace('Request POST Data: {0}'.format(pprint.pformat(data)))

    if header_file is not None:
        header_tpl = _render(
            header_file, header_render, header_renderer, template_dict, opts
        )
        if isinstance(header_tpl, dict):
            header_dict = header_tpl
        else:
            header_list = header_tpl.splitlines()

    if header_dict is None:
        header_dict = {}

    if header_list is None:
        header_list = []

    if cookie_jar is None:
        cookie_jar = os.path.join(opts.get('cachedir', syspaths.CACHE_DIR), 'cookies.txt')
    if session_cookie_jar is None:
        session_cookie_jar = os.path.join(opts.get('cachedir', syspaths.CACHE_DIR), 'cookies.session.p')

    if persist_session is True and HAS_MSGPACK:
        # TODO: This is hackish; it will overwrite the session cookie jar with
        # all cookies from this one connection, rather than behaving like a
        # proper cookie jar. Unfortunately, since session cookies do not
        # contain expirations, they can't be stored in a proper cookie jar.
        if os.path.isfile(session_cookie_jar):
            with salt.utils.fopen(session_cookie_jar, 'r') as fh_:
                session_cookies = msgpack.load(fh_)
            if isinstance(session_cookies, dict):
                header_dict.update(session_cookies)
        else:
            with salt.utils.fopen(session_cookie_jar, 'w') as fh_:
                msgpack.dump('', fh_)

    for header in header_list:
        comps = header.split(':')
        if len(comps) < 2:
            continue
        header_dict[comps[0].strip()] = comps[1].strip()

    if not auth:
        if username and password:
            auth = (username, password)

    if agent == USERAGENT:
        agent = '{0} http.query()'.format(agent)
    header_dict['User-agent'] = agent

    if backend == 'requests':
        sess = requests.Session()
        sess.auth = auth
        sess.headers.update(header_dict)
        log.trace('Request Headers: {0}'.format(sess.headers))
        sess_cookies = sess.cookies
        sess.verify = verify_ssl
    elif backend == 'urllib2':
        sess_cookies = None
    else:
        # Tornado
        sess_cookies = None

    if cookies is not None:
        if cookie_format == 'mozilla':
            sess_cookies = salt.ext.six.moves.http_cookiejar.MozillaCookieJar(cookie_jar)
        else:
            sess_cookies = salt.ext.six.moves.http_cookiejar.LWPCookieJar(cookie_jar)
        if not os.path.isfile(cookie_jar):
            sess_cookies.save()
        sess_cookies.load()

    if test is True:
        if test_url is None:
            return {}
        else:
            url = test_url
            ret['test'] = True

    if backend == 'requests':
        req_kwargs = {}
        if stream is True:
            if requests.__version__[0] == '0':
                # 'stream' was called 'prefetch' before 1.0, with flipped meaning
                req_kwargs['prefetch'] = False
            else:
                req_kwargs['stream'] = True

        # Client-side cert handling
        if cert is not None:
            if isinstance(cert, six.string_types):
                if os.path.exists(cert):
                    req_kwargs['cert'] = cert
            elif isinstance(cert, tuple):
                if os.path.exists(cert[0]) and os.path.exists(cert[1]):
                    req_kwargs['cert'] = cert
            else:
                log.error('The client-side certificate path that was passed is '
                          'not valid: {0}'.format(cert))

        result = sess.request(
            method, url, params=params, data=data, **req_kwargs
        )
        result.raise_for_status()
        if stream is True or handle is True:
            return {
                'handle': result,
                'body': result.content,
            }

        log.debug('Final URL location of Response: {0}'.format(sanitize_url(result.url, hide_fields)))

        result_status_code = result.status_code
        result_headers = result.headers
        result_text = result.text
        result_cookies = result.cookies
        ret['body'] = result.content
    elif backend == 'urllib2':
        request = urllib_request.Request(url_full, data)
        handlers = [
            urllib_request.HTTPHandler,
            urllib_request.HTTPCookieProcessor(sess_cookies)
        ]

        if url.startswith('https'):
            hostname = request.get_host()
            handlers[0] = urllib_request.HTTPSHandler(1)
            if not HAS_MATCHHOSTNAME:
                log.warn(('match_hostname() not available, SSL hostname checking '
                         'not available. THIS CONNECTION MAY NOT BE SECURE!'))
            elif verify_ssl is False:
                log.warn(('SSL certificate verification has been explicitly '
                         'disabled. THIS CONNECTION MAY NOT BE SECURE!'))
            else:
                if ':' in hostname:
                    hostname, port = hostname.split(':')
                else:
                    port = 443
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((hostname, int(port)))
                sockwrap = ssl.wrap_socket(
                    sock,
                    ca_certs=ca_bundle,
                    cert_reqs=ssl.CERT_REQUIRED
                )
                try:
                    match_hostname(sockwrap.getpeercert(), hostname)
                except CertificateError as exc:
                    ret['error'] = (
                        'The certificate was invalid. '
                        'Error returned was: {0}'.format(
                            pprint.pformat(exc)
                        )
                    )
                    return ret

                # Client-side cert handling
                if cert is not None:
                    cert_chain = None
                    if isinstance(cert, six.string_types):
                        if os.path.exists(cert):
                            cert_chain = (cert)
                    elif isinstance(cert, tuple):
                        if os.path.exists(cert[0]) and os.path.exists(cert[1]):
                            cert_chain = cert
                    else:
                        log.error('The client-side certificate path that was '
                                  'passed is not valid: {0}'.format(cert))
                        return
                    if hasattr(ssl, 'SSLContext'):
                        # Python >= 2.7.9
                        context = ssl.SSLContext.load_cert_chain(*cert_chain)
                        handlers.append(urllib_request.HTTPSHandler(context=context))  # pylint: disable=E1123
                    else:
                        # Python < 2.7.9
                        cert_kwargs = {
                            'host': request.get_host(),
                            'port': port,
                            'cert_file': cert_chain[0]
                        }
                        if len(cert_chain) > 1:
                            cert_kwargs['key_file'] = cert_chain[1]
                        handlers[0] = salt.ext.six.moves.http_client.HTTPSConnection(**cert_kwargs)

        opener = urllib_request.build_opener(*handlers)
        for header in header_dict:
            request.add_header(header, header_dict[header])
        request.get_method = lambda: method
        try:
            result = opener.open(request)
        except URLError as exc:
            return {'Error': str(exc)}
        if stream is True or handle is True:
            return {
                'handle': result,
                'body': result.content,
            }

        result_status_code = result.code
        result_headers = result.headers.headers
        result_text = result.read()
        ret['body'] = result_text
    else:
        # Tornado
        req_kwargs = {}

        # Client-side cert handling
        if cert is not None:
            if isinstance(cert, six.string_types):
                if os.path.exists(cert):
                    req_kwargs['client_cert'] = cert
            elif isinstance(cert, tuple):
                if os.path.exists(cert[0]) and os.path.exists(cert[1]):
                    req_kwargs['client_cert'] = cert[0]
                    req_kwargs['client_key'] = cert[1]
            else:
                log.error('The client-side certificate path that was passed is '
                          'not valid: {0}'.format(cert))

        if verify_ssl:
            req_kwargs['ca_certs'] = ca_bundle

        max_body = opts.get('http_max_body', salt.config.DEFAULT_MINION_OPTS['http_max_body'])
        timeout = opts.get('http_request_timeout', salt.config.DEFAULT_MINION_OPTS['http_request_timeout'])

        client_argspec = inspect.getargspec(tornado.simple_httpclient.SimpleAsyncHTTPClient.initialize)
        supports_max_body_size = 'max_body_size' in client_argspec.args

        try:
            if supports_max_body_size:
                result = HTTPClient(max_body_size=max_body).fetch(
                    url_full,
                    method=method,
                    headers=header_dict,
                    auth_username=username,
                    auth_password=password,
                    body=data,
                    validate_cert=verify_ssl,
                    allow_nonstandard_methods=True,
                    streaming_callback=streaming_callback,
                    request_timeout=timeout,
                    **req_kwargs
                )
            else:
                result = HTTPClient().fetch(
                    url_full,
                    method=method,
                    headers=header_dict,
                    auth_username=username,
                    auth_password=password,
                    body=data,
                    validate_cert=verify_ssl,
                    allow_nonstandard_methods=True,
                    streaming_callback=streaming_callback,
                    request_timeout=timeout,
                    **req_kwargs
                )
        except tornado.httpclient.HTTPError as exc:
            ret['status'] = exc.code
            ret['error'] = str(exc)
            return ret

        if stream is True or handle is True:
            return {
                'handle': result,
                'body': result.body,
            }

        result_status_code = result.code
        result_headers = result.headers
        result_text = result.body
        ret['body'] = result.body
        if 'Set-Cookie' in result_headers.keys() and cookies is not None:
            result_cookies = parse_cookie_header(result_headers['Set-Cookie'])
            for item in result_cookies:
                sess_cookies.set_cookie(item)
        else:
            result_cookies = None

    if isinstance(result_headers, list):
        result_headers_dict = {}
        for header in result_headers:
            comps = header.split(':')
            result_headers_dict[comps[0].strip()] = ':'.join(comps[1:]).strip()
        result_headers = result_headers_dict

    log.debug('Response Status Code: {0}'.format(result_status_code))
    log.trace('Response Headers: {0}'.format(result_headers))
    log.trace('Response Cookies: {0}'.format(sess_cookies))
    try:
        log.trace('Response Text: {0}'.format(result_text))
    except UnicodeEncodeError as exc:
        log.trace(('Cannot Trace Log Response Text: {0}. This may be due to '
                  'incompatibilities between requests and logging.').format(exc))

    if text_out is not None and os.path.exists(text_out):
        with salt.utils.fopen(text_out, 'w') as tof:
            tof.write(result_text)

    if headers_out is not None and os.path.exists(headers_out):
        with salt.utils.fopen(headers_out, 'w') as hof:
            hof.write(result_headers)

    if cookies is not None:
        sess_cookies.save()

    if persist_session is True and HAS_MSGPACK:
        # TODO: See persist_session above
        if 'set-cookie' in result_headers:
            with salt.utils.fopen(session_cookie_jar, 'w') as fh_:
                session_cookies = result_headers.get('set-cookie', None)
                if session_cookies is not None:
                    msgpack.dump({'Cookie': session_cookies}, fh_)
                else:
                    msgpack.dump('', fh_)

    if status is True:
        ret['status'] = result_status_code

    if headers is True:
        ret['headers'] = result_headers

    if decode is True:
        if decode_type == 'auto':
            content_type = result_headers.get(
                'content-type', 'application/json'
            )
            if 'xml' in content_type:
                decode_type = 'xml'
            elif 'json' in content_type:
                decode_type = 'json'
            else:
                decode_type = 'plain'

        valid_decodes = ('json', 'xml', 'plain')
        if decode_type not in valid_decodes:
            ret['error'] = (
                'Invalid decode_type specified. '
                'Valid decode types are: {0}'.format(
                    pprint.pformat(valid_decodes)
                )
            )
            log.error(ret['error'])
            return ret

        if decode_type == 'json':
            ret['dict'] = json.loads(salt.utils.to_str(result_text))
        elif decode_type == 'xml':
            ret['dict'] = []
            items = ET.fromstring(result_text)
            for item in items:
                ret['dict'].append(xml.to_dict(item))
        else:
            text = True

        if decode_out and os.path.exists(decode_out):
            with salt.utils.fopen(decode_out, 'w') as dof:
                dof.write(result_text)

    if text is True:
        ret['text'] = result_text

    return ret