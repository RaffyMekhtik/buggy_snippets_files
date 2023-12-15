def _get_shift_kernel(ndim, large_int, yshape, mode, cval=0.0, order=1,
                      integer_output=False):
    in_params = 'raw X x, raw W shift'
    out_params = 'Y y'
    operation, name = _generate_interp_custom(
        coord_func=_get_coord_shift,
        ndim=ndim,
        large_int=large_int,
        yshape=yshape,
        mode=mode,
        cval=cval,
        order=order,
        name='shift',
        integer_output=integer_output,
    )
    return cupy.ElementwiseKernel(in_params, out_params, operation, name,
                                  preamble=math_constants_preamble)