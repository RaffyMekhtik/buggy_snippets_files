def os_walk(top, *args, **kwargs):
    '''
    This is a helper than ensures that all paths returned from os.walk are
    unicode.
    '''
    for item in os.walk(salt.utils.stringutils.to_str(top), *args, **kwargs):
        yield salt.utils.data.decode(item, preserve_tuples=True)