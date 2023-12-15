def call_parallel_gufunc(lowerer, cres, gu_signature, outer_sig, expr_args,
                    loop_ranges, array_size_vars, redvars, reddict, init_block):
    '''
    Adds the call to the gufunc function from the main function.
    '''
    context = lowerer.context
    builder = lowerer.builder
    library = lowerer.library

    from .parallel import (ParallelGUFuncBuilder, build_gufunc_wrapper,
                                get_thread_count, _launch_threads, _init)

    if config.DEBUG_ARRAY_OPT:
        print("make_parallel_loop")
        print("args = ", expr_args)
        print("outer_sig = ", outer_sig.args, outer_sig.return_type,
                                outer_sig.recvr, outer_sig.pysig)
        print("loop_ranges = ", loop_ranges)

    # Build the wrapper for GUFunc
    args, return_type = sigutils.normalize_signature(outer_sig)
    llvm_func = cres.library.get_function(cres.fndesc.llvm_func_name)
    sin, sout = gu_signature

    # These are necessary for build_gufunc_wrapper to find external symbols
    _launch_threads()
    _init()

    wrapper_ptr, env, wrapper_name = build_gufunc_wrapper(llvm_func, cres, sin,
                                                            sout, {})
    cres.library._ensure_finalized()

    if config.DEBUG_ARRAY_OPT:
        print("parallel function = ", wrapper_name, cres)

    # loadvars for loop_ranges
    def load_range(v):
        if isinstance(v, ir.Var):
            return lowerer.loadvar(v.name)
        else:
            return context.get_constant(types.intp, v)

    num_dim = len(loop_ranges)
    for i in range(num_dim):
        start, stop, step = loop_ranges[i]
        start = load_range(start)
        stop = load_range(stop)
        assert(step == 1) # We do not support loop steps other than 1
        step = load_range(step)
        loop_ranges[i] = (start, stop, step)

        if config.DEBUG_ARRAY_OPT:
            print("call_parallel_gufunc loop_ranges[{}] = ".format(i), start,
                stop, step)
            cgutils.printf(builder, "loop range[{}]: %d %d (%d)\n".format(i),
                start, stop, step)


    # Commonly used LLVM types and constants
    byte_t = lc.Type.int(8)
    byte_ptr_t = lc.Type.pointer(byte_t)
    byte_ptr_ptr_t = lc.Type.pointer(byte_ptr_t)
    intp_t = context.get_value_type(types.intp)
    uintp_t = context.get_value_type(types.uintp)
    intp_ptr_t = lc.Type.pointer(intp_t)
    zero = context.get_constant(types.intp, 0)
    one = context.get_constant(types.intp, 1)
    sizeof_intp = context.get_abi_sizeof(intp_t)

    # Prepare sched, first pop it out of expr_args, outer_sig, and gu_signature
    sched_name = expr_args.pop(0)
    sched_typ = outer_sig.args[0]
    sched_sig = sin.pop(0)

    # Call do_scheduling with appropriate arguments
    dim_starts = cgutils.alloca_once(builder, intp_t,
            size = context.get_constant(types.intp, num_dim), name = "dims")
    dim_stops = cgutils.alloca_once(builder, intp_t,
            size = context.get_constant(types.intp, num_dim), name = "dims")
    for i in range(num_dim):
        start, stop, step = loop_ranges[i]
        # substract 1 because do-scheduling takes inclusive ranges
        stop = builder.sub(stop, one)
        builder.store(start, builder.gep(dim_starts,
            [context.get_constant(types.intp, i)]))
        builder.store(stop, builder.gep(dim_stops,
            [context.get_constant(types.intp, i)]))
    sched_size = get_thread_count() * num_dim * 2
    sched = cgutils.alloca_once(builder, intp_t,
            size = context.get_constant(types.intp, sched_size), name = "sched")
    debug_flag = 1 if config.DEBUG_ARRAY_OPT else 0
    scheduling_fnty = lc.Type.function(intp_ptr_t,
        [intp_t, intp_ptr_t, intp_ptr_t, uintp_t, intp_ptr_t, intp_t])
    do_scheduling = builder.module.get_or_insert_function(scheduling_fnty,
                                                        name="do_scheduling")
    builder.call(do_scheduling, [context.get_constant(types.intp, num_dim),
        dim_starts, dim_stops,
        context.get_constant(types.uintp, get_thread_count()), sched,
        context.get_constant(types.intp, debug_flag)])

    # init reduction array allocation here.
    nredvars = len(redvars)
    ninouts = len(expr_args) - nredvars
    redarrs = []
    for i in range(nredvars):
        # arr = expr_args[-(nredvars - i)]
        val = lowerer.loadvar(redvars[i])
        # cgutils.printf(builder, "nredvar(" + redvars[i] + ") = %d\n", val)
        typ = context.get_value_type(lowerer.fndesc.typemap[redvars[i]])
        size = get_thread_count()
        arr = cgutils.alloca_once(builder, typ,
                                size = context.get_constant(types.intp, size))
        redarrs.append(arr)
        for j in range(size):
            dst = builder.gep(arr, [ context.get_constant(types.intp, j) ])
            builder.store(val, dst)

    if config.DEBUG_ARRAY_OPT:
      for i in range(get_thread_count()):
        cgutils.printf(builder, "sched[" + str(i) + "] = ")
        for j in range(num_dim * 2):
            cgutils.printf(builder, "%d ", builder.load(builder.gep(sched,
                    [context.get_constant(types.intp, i * num_dim * 2 + j)])))
        cgutils.printf(builder, "\n")

    # Prepare arguments: args, shapes, steps, data
    all_args = [ lowerer.loadvar(x) for x in expr_args[:ninouts] ] + redarrs
    num_args = len(all_args)
    num_inps = len(sin) + 1
    args = cgutils.alloca_once(builder, byte_ptr_t,
        size = context.get_constant(types.intp, 1 + num_args), name = "pargs")
    array_strides = []
    # sched goes first
    builder.store(builder.bitcast(sched, byte_ptr_t), args)
    array_strides.append(context.get_constant(types.intp, sizeof_intp))
    # followed by other arguments
    for i in range(num_args):
        arg = all_args[i]
        aty = outer_sig.args[i + 1] # skip first argument sched
        dst = builder.gep(args, [context.get_constant(types.intp, i + 1)])
        if i >= ninouts: # reduction variables
            builder.store(builder.bitcast(arg, byte_ptr_t), dst)
        elif isinstance(aty, types.ArrayCompatible):
            ary = context.make_array(aty)(context, builder, arg)
            strides = cgutils.unpack_tuple(builder, ary.strides, aty.ndim)
            for j in range(len(strides)):
                array_strides.append(strides[j])
            builder.store(builder.bitcast(ary.data, byte_ptr_t), dst)
        else:
            if i < num_inps:
                # Scalar input, need to store the value in an array of size 1
                typ = context.get_data_type(aty) if aty != types.boolean else lc.Type.int(1)
                ptr = cgutils.alloca_once(builder, typ)
                builder.store(arg, ptr)
            else:
                # Scalar output, must allocate
                typ = context.get_data_type(aty) if aty != types.boolean else lc.Type.int(1)
                ptr = cgutils.alloca_once(builder, typ)
            builder.store(builder.bitcast(ptr, byte_ptr_t), dst)

    # Next, we prepare the individual dimension info recorded in gu_signature
    sig_dim_dict = {}
    occurances = []
    occurances = [sched_sig[0]]
    sig_dim_dict[sched_sig[0]] = context.get_constant(types.intp, 2 * num_dim)
    for var, arg, aty, gu_sig in zip(expr_args[:ninouts], all_args[:ninouts],
                                        outer_sig.args[1:], sin + sout):
        if config.DEBUG_ARRAY_OPT:
            print("var = ", var, " gu_sig = ", gu_sig)
        i = 0
        for dim_sym in gu_sig:
            dim = array_size_vars[var][i]
            if isinstance(dim, ir.Var):
                sig_dim_dict[dim_sym] = lowerer.loadvar(dim.name)
            elif isinstance(dim, int):
                sig_dim_dict[dim_sym] = context.get_constant(types.intp, dim)
            else:
                # raise NotImplementedError("wrong dimension value encoutered: ", dim)
                if config.DEBUG_ARRAY_OPT:
                    print("var = ", var, " type = ", aty)
                ary = context.make_array(aty)(context, builder, arg)
                shapes = cgutils.unpack_tuple(builder, ary.strides, aty.ndim)
                sig_dim_dict[dim_sym] = shapes[i]
            if not (dim_sym in occurances):
                if config.DEBUG_ARRAY_OPT:
                    print("dim_sym = ", dim_sym, ", size = ", array_size_vars[var][i])
                occurances.append(dim_sym)
            i = i + 1

    # Prepare shapes, which is a single number (outer loop size), followed by the size of individual shape variables.
    nshapes = len(sig_dim_dict) + 1
    shapes = cgutils.alloca_once(builder, intp_t, size = nshapes, name = "pshape")
    # For now, outer loop size is the same as number of threads
    builder.store(context.get_constant(types.intp, get_thread_count()), shapes)
    # Individual shape variables go next
    i = 1
    for dim_sym in occurances:
        if config.DEBUG_ARRAY_OPT:
            cgutils.printf(builder, dim_sym + " = %d\n", sig_dim_dict[dim_sym])
        builder.store(sig_dim_dict[dim_sym], builder.gep(shapes,
                                    [ context.get_constant(types.intp, i) ]))
        i = i + 1

    # Prepare steps for each argument. Note that all steps are counted in bytes.
    num_steps = num_args + 1 + len(array_strides)
    steps = cgutils.alloca_once(builder, intp_t,
            size = context.get_constant(types.intp, num_steps), name = "psteps")
    # First goes the step size for sched, which is 2 * num_dim
    builder.store(context.get_constant(types.intp, 2 * num_dim * sizeof_intp),
                                                                        steps)
    # The steps for all others are 0. (TODO: except reduction results)
    for i in range(num_args):
        if i >= ninouts: # steps for reduction vars are abi_sizeof(typ)
            j = i - ninouts
            typ = context.get_value_type(lowerer.fndesc.typemap[redvars[j]])
            sizeof = context.get_abi_sizeof(typ)
            stepsize = context.get_constant(types.intp, sizeof)
        else:
            # steps are strides
            stepsize = zero
        dst = builder.gep(steps, [context.get_constant(types.intp, 1 + i)])
        builder.store(stepsize, dst)
    for j in range(len(array_strides)):
        dst = builder.gep(steps, [context.get_constant(types.intp, 1 + num_args + j)])
        builder.store(array_strides[j], dst)

    # prepare data
    data = builder.inttoptr(zero, byte_ptr_t)

    fnty = lc.Type.function(lc.Type.void(), [byte_ptr_ptr_t, intp_ptr_t,
                                             intp_ptr_t, byte_ptr_t])
    fn = builder.module.get_or_insert_function(fnty, name=wrapper_name)
    if config.DEBUG_ARRAY_OPT:
        cgutils.printf(builder, "before calling kernel %p\n", fn)
    result = builder.call(fn, [args, shapes, steps, data])
    if config.DEBUG_ARRAY_OPT:
        cgutils.printf(builder, "after calling kernel %p\n", fn)

    scope = init_block.scope
    loc = init_block.loc
    calltypes = lowerer.fndesc.calltypes
    # Accumulate all reduction arrays back to a single value
    for i in range(get_thread_count()):
        for name, arr in zip(redvars, redarrs):
            tmpname = mk_unique_var(name)
            op, imop = reddict[name]
            src = builder.gep(arr, [context.get_constant(types.intp, i)])
            val = builder.load(src)
            vty = lowerer.fndesc.typemap[name]
            lowerer.fndesc.typemap[tmpname] = vty
            lowerer.storevar(val, tmpname)
            accvar = ir.Var(scope, name, loc)
            tmpvar = ir.Var(scope, tmpname, loc)
            acc_call = ir.Expr.inplace_binop(op, imop, accvar, tmpvar, loc)
            calltypes[acc_call] = signature(vty, vty, vty)
            inst = ir.Assign(acc_call, accvar, loc)
            lowerer.lower_inst(inst)

    # TODO: scalar output must be assigned back to corresponding output variables
    return