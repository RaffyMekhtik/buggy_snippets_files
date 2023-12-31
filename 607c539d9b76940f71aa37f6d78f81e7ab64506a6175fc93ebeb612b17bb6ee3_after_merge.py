def jit(func_or_sig=None, argtypes=None, device=False, inline=False, bind=True,
        link=[], debug=None, **kws):
    """
    JIT compile a python function conforming to the CUDA Python specification.
    If a signature is supplied, then a function is returned that takes a
    function to compile. If

    :param func_or_sig: A function to JIT compile, or a signature of a function
       to compile. If a function is supplied, then an :class:`AutoJitCUDAKernel`
       is returned. If a signature is supplied, then a function which takes a
       function to compile and returns an :class:`AutoJitCUDAKernel` is
       returned.

       .. note:: A kernel cannot have any return value.
    :type func_or_sig: function or numba.typing.Signature
    :param device: Indicates whether this is a device function.
    :type device: bool
    :param bind: Force binding to CUDA context immediately
    :type bind: bool
    :param link: A list of files containing PTX source to link with the function
    :type link: list
    :param debug: If True, check for exceptions thrown when executing the
       kernel. Since this degrades performance, this should only be used for
       debugging purposes.  Defaults to False.  (The default value can be
       overriden by setting environment variable ``NUMBA_CUDA_DEBUGINFO=1``.)
    :param fastmath: If true, enables flush-to-zero and fused-multiply-add,
       disables precise division and square root. This parameter has no effect
       on device function, whose fastmath setting depends on the kernel function
       from which they are called.
    :param max_registers: Limit the kernel to using at most this number of
       registers per thread. Useful for increasing occupancy.
    """
    debug = config.CUDA_DEBUGINFO_DEFAULT if debug is None else debug

    if link and config.ENABLE_CUDASIM:
        raise NotImplementedError('Cannot link PTX in the simulator')

    if 'boundscheck' in kws:
        raise NotImplementedError("bounds checking is not supported for CUDA")

    fastmath = kws.get('fastmath', False)
    if argtypes is None and not sigutils.is_signature(func_or_sig):
        if func_or_sig is None:
            if config.ENABLE_CUDASIM:
                def autojitwrapper(func):
                    return FakeCUDAKernel(func, device=device, fastmath=fastmath,
                                          debug=debug)
            else:
                def autojitwrapper(func):
                    return jit(func, device=device, bind=bind, debug=debug,
                               **kws)

            return autojitwrapper
        # func_or_sig is a function
        else:
            if config.ENABLE_CUDASIM:
                return FakeCUDAKernel(func_or_sig, device=device, fastmath=fastmath,
                                      debug=debug)
            elif device:
                return jitdevice(func_or_sig, debug=debug, **kws)
            else:
                targetoptions = kws.copy()
                targetoptions['debug'] = debug
                return AutoJitCUDAKernel(func_or_sig, bind=bind, targetoptions=targetoptions)

    else:
        if config.ENABLE_CUDASIM:
            def jitwrapper(func):
                return FakeCUDAKernel(func, device=device, fastmath=fastmath,
                                      debug=debug)
            return jitwrapper

        restype, argtypes = convert_types(func_or_sig, argtypes)

        if restype and not device and restype != types.void:
            raise TypeError("CUDA kernel must have void return type.")

        def kernel_jit(func):
            kernel = compile_kernel(func, argtypes, link=link, debug=debug,
                                    inline=inline, fastmath=fastmath)

            # Force compilation for the current context
            if bind:
                kernel.bind()

            return kernel

        def device_jit(func):
            return compile_device(func, restype, argtypes, inline=inline,
                                  debug=debug)

        if device:
            return device_jit
        else:
            return kernel_jit