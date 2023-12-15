def ewmvar(arg, com=None, span=None, halflife=None, min_periods=0, bias=False,
           freq=None, how=None):
    com = _get_center_of_mass(com, span, halflife)
    arg = _conv_timerule(arg, freq, how)
    moment2nd = ewma(arg * arg, com=com, min_periods=min_periods)
    moment1st = ewma(arg, com=com, min_periods=min_periods)

    result = moment2nd - moment1st ** 2
    if not bias:
        result *= (1.0 + 2.0 * com) / (2.0 * com)

    return result