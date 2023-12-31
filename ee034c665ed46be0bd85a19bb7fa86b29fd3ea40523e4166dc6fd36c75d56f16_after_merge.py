def pi_check(inpt, eps=1e-6, output='text', ndigits=5):
    """ Computes if a number is close to an integer
    fraction or multiple of PI and returns the
    corresponding string.

    Args:
        inpt (float): Number to check.
        eps (float): EPS to check against.
        output (str): Options are 'text' (default),
                      'latex', and 'mpl'.
        ndigits (int): Number of digits to print
                       if returning raw inpt.

    Returns:
        str: string representation of output.

    Raises:
        QiskitError: if output is not a valid option.
    """
    if isinstance(inpt, ParameterExpression):
        return str(inpt)
    inpt = float(inpt)
    if abs(inpt) < 1e-14:
        return str(0)
    val = inpt / np.pi

    if output == 'text':
        pi = 'pi'
    elif output == 'latex':
        pi = '\\pi'
    elif output == 'mpl':
        pi = '$\\pi$'
    else:
        raise QiskitError('pi_check parameter output should be text, latex, or mpl')

    if abs(val) >= 1:
        if abs(val % 1) < eps:
            val = int(round(val))
            if val == 1:
                str_out = '{}'.format(pi)
            elif val == -1:
                str_out = '-{}'.format(pi)
            else:
                str_out = '{}{}'.format(val, pi)
            return str_out

    val = np.pi / inpt
    if abs(abs(val) - abs(round(val))) < eps:
        val = int(round(val))
        if val > 0:
            str_out = '{}/{}'.format(pi, val)
        else:
            str_out = '-{}/{}'.format(pi, abs(val))
        return str_out

    # Look for all fracs in 8
    abs_val = abs(inpt)
    frac = np.where(np.abs(abs_val - FRAC_MESH) < 1e-8)
    if frac[0].shape[0]:
        numer = int(frac[1][0]) + 1
        denom = int(frac[0][0]) + 1
        if inpt < 0:
            numer *= -1

        if numer == 1 and denom == 1:
            str_out = '{}'.format(pi)
        elif numer == -1 and denom == 1:
            str_out = '-{}'.format(pi)
        elif numer == 1:
            str_out = '{}/{}'.format(pi, denom)
        elif numer == -1:
            str_out = '-{}/{}'.format(pi, denom)
        elif denom == 1:
            str_out = '{}/{}'.format(numer, pi)
        else:
            str_out = '{}{}/{}'.format(numer, pi, denom)

        return str_out
    # nothing found
    str_out = '%.{}g'.format(ndigits) % inpt
    return str_out