def _try_peername(sock):
    try:
        pn = sock.getpeername()
        if pn:
            return '%s:%s' % (pn[0], pn[1])
    except socket.error:
        _, e = sys.exc_info()[:2]
        if e.args[0] == errno.EINVAL:
            debug2("_try_peername error: sock.getpeername() %s\nsocket is probably closed.\n" % e)
            pass
        elif e.args[0] not in (errno.ENOTCONN, errno.ENOTSOCK):
            raise
    except AttributeError:
        pass
    return 'unknown'