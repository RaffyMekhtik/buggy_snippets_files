def get_uniformed_tracker_url(tracker_url):
    """
    Parse a tracker url of basestring type.

    The following checks and transformations are applied to the url:
        - Check if the url is valid unicode data
        - Strip whitespaces
        - Strip a trailing '/'
        - Check that the port is
            - provided in case of UDP
            - in range in case of HTTP (implicitly done in the `urlparse` function)
        - If it is a url for a HTTP tracker, don't include the default port HTTP_PORT

    Examples:
        udp://tracker.openbittorrent.com:80
        http://tracker.openbittorrent.com:80/announce

    :param tracker_url: a basestring url for either a UDP or HTTP tracker
    :return: the tracker in a uniform format <type>://<host>:<port>/<page>
    """
    assert isinstance(tracker_url, basestring), u"tracker_url is not a basestring: %s" % type(tracker_url)

    # check if the URL is valid unicode data
    try:
        tracker_url = unicode(tracker_url)
    except UnicodeDecodeError:
        return None

    url = urlparse(tracker_url)

    # scheme must be either UDP or HTTP
    if url.scheme == 'udp' or url.scheme == 'http':
        uniformed_scheme = url.scheme
    else:
        return None

    uniformed_hostname = url.hostname

    if not url.port:
        # UDP trackers must have a port
        if url.scheme == 'udp':
            return None
        # HTTP trackers default to port HTTP_PORT
        elif url.scheme == 'http':
            uniformed_port = HTTP_PORT
    else:
        uniformed_port = url.port

    # UDP trackers have no path
    if url.scheme == 'udp':
        uniformed_path = ''
    else:
        uniformed_path = url.path.rstrip('/')
    # HTTP trackers must have a path
    if url.scheme == 'http' and not url.path:
        return None

    if url.scheme == 'http' and uniformed_port == HTTP_PORT:
        uniformed_url = u'%s://%s%s' % (uniformed_scheme, uniformed_hostname, uniformed_path)
    else:
        uniformed_url = u'%s://%s:%d%s' % (uniformed_scheme, uniformed_hostname, uniformed_port, uniformed_path)

    return uniformed_url