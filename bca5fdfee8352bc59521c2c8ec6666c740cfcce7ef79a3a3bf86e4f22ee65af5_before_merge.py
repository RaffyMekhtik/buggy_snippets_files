def _dec2hex(decval):
    '''
    Converts decimal values to nicely formatted hex strings
    '''
    return _pretty_hex('{:X}'.format(decval))