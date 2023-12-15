def _lower_parfor_parallel(lowerer, parfor):
    """Lowerer that handles LLVM code generation for parfor.
    This function lowers a parfor IR node to LLVM.
    The general approach is as follows:
    1) The code from the parfor's init block is lowered normally
       in the context of the current function.
    2) The body of the parfor is transformed into a gufunc function.
    3) Code is inserted into the main function that calls do_scheduling
       to divide the iteration space for each thread, allocates
       reduction arrays, calls the gufunc function, and then invokes
       the reduction function across the reduction arrays to produce
       the final reduction values.
    """
    typingctx = lowerer.context.typing_context
    targetctx = lowerer.context
    typemap = lowerer.fndesc.typemap

    if config.DEBUG_ARRAY_OPT:
        print("_lower_parfor_parallel")
        parfor.dump()

    # produce instructions for init_block
    if config.DEBUG_ARRAY_OPT:
        print("init_block = ", parfor.init_block, " ", type(parfor.init_block))
    for instr in parfor.init_block.body:
        if config.DEBUG_ARRAY_OPT:
            print("lower init_block instr = ", instr)
        lowerer.lower_inst(instr)

    # run get_parfor_outputs() and get_parfor_reductions() before gufunc creation
    # since Jumps are modified so CFG of loop_body dict will become invalid
    parfor_output_arrays = numba.parfor.get_parfor_outputs(parfor)
    parfor_redvars, parfor_reddict = numba.parfor.get_parfor_reductions(parfor)
    # compile parfor body as a separate function to be used with GUFuncWrapper
    flags = compiler.Flags()
    flags.set('error_model', 'numpy')
    func, func_args, func_sig = _create_gufunc_for_parfor_body(lowerer, parfor, typemap, typingctx, targetctx, flags, {})

    # get the shape signature
    array_shape_classes = parfor.array_analysis.array_shape_classes
    func_args = ['sched'] + func_args
    num_reductions = len(parfor_redvars)
    num_inputs = len(func_args) - len(parfor_output_arrays) - num_reductions
    if config.DEBUG_ARRAY_OPT:
        print("num_inputs = ", num_inputs)
        print("parfor_outputs = ", parfor_output_arrays)
        print("parfor_redvars = ", parfor_redvars)
    gu_signature = _create_shape_signature(array_shape_classes, num_inputs, num_reductions, func_args, func_sig)
    if config.DEBUG_ARRAY_OPT:
        print("gu_signature = ", gu_signature)

    # call the func in parallel by wrapping it with ParallelGUFuncBuilder
    loop_ranges = [(l.start, l.stop, l.step) for l in parfor.loop_nests]
    if config.DEBUG_ARRAY_OPT:
        print("loop_nests = ", parfor.loop_nests)
        print("loop_ranges = ", loop_ranges)
    array_size_vars = parfor.array_analysis.array_size_vars
    if config.DEBUG_ARRAY_OPT:
        print("array_size_vars = ", sorted(array_size_vars.items()))
    call_parallel_gufunc(lowerer, func, gu_signature, func_sig, func_args, loop_ranges, array_size_vars, parfor_redvars, parfor_reddict, parfor.init_block)
    if config.DEBUG_ARRAY_OPT:
        sys.stdout.flush()