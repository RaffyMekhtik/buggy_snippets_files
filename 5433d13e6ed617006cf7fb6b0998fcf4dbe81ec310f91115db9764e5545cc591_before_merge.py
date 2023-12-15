def init():
    global cache

    if 'PWNLIB_NOTERM' not in os.environ:
        # Fix for BPython
        try:
            curses.setupterm()
        except curses.error as e:
            import traceback
            print('Warning:', ''.join(traceback.format_exception_only(e.__class__, e)), file=sys.stderr)

    cache = {}
    # Manually add reset sequence into the cache.
    # Can't look it up using tigetstr.
    cache['reset'] = '\x1b[m'