    def process_environ(self, environ):
        def _readenv(name, ctor, default):
            value = environ.get(name)
            if value is None:
                return default() if callable(default) else default
            try:
                return ctor(value)
            except Exception:
                warnings.warn("environ %s defined but failed to parse '%s'" %
                              (name, value), RuntimeWarning)
                return default

        def optional_str(x):
            return str(x) if x is not None else None

        # developer mode produces full tracebacks, disables help instructions
        DEVELOPER_MODE = _readenv("NUMBA_DEVELOPER_MODE", int, 0)

        # disable performance warnings, will switch of the generation of
        # warnings of the class NumbaPerformanceWarning
        DISABLE_PERFORMANCE_WARNINGS = _readenv(
            "NUMBA_DISABLE_PERFORMANCE_WARNINGS", int, 0)

        # Flag to enable full exception reporting
        FULL_TRACEBACKS = _readenv(
            "NUMBA_FULL_TRACEBACKS", int, DEVELOPER_MODE)

        # Show help text when an error occurs
        SHOW_HELP = _readenv("NUMBA_SHOW_HELP", int, 0)

        # The color scheme to use for error messages, default is no color
        # just bold fonts in use.
        COLOR_SCHEME = _readenv("NUMBA_COLOR_SCHEME", str, "no_color")

        # Whether to globally enable bounds checking. The default None means
        # to use the value of the flag to @njit. 0 or 1 overrides the flag
        # globally.
        BOUNDSCHECK = _readenv("NUMBA_BOUNDSCHECK", int, None)

        # Whether to always warn about potential uninitialized variables
        # because static controlflow analysis cannot find a definition
        # in one or more of the incoming paths.
        ALWAYS_WARN_UNINIT_VAR = _readenv(
            "NUMBA_ALWAYS_WARN_UNINIT_VAR", int, 0,
        )

        # Debug flag to control compiler debug print
        DEBUG = _readenv("NUMBA_DEBUG", int, 0)

        # DEBUG print IR after pass names
        DEBUG_PRINT_AFTER = _readenv("NUMBA_DEBUG_PRINT_AFTER", str, "none")

        # DEBUG print IR before pass names
        DEBUG_PRINT_BEFORE = _readenv("NUMBA_DEBUG_PRINT_BEFORE", str, "none")

        # DEBUG print IR before and after pass names
        DEBUG_PRINT_WRAP = _readenv("NUMBA_DEBUG_PRINT_WRAP", str, "none")

        # Highlighting in intermediate dumps
        HIGHLIGHT_DUMPS = _readenv("NUMBA_HIGHLIGHT_DUMPS", int, 0)

        # JIT Debug flag to trigger IR instruction print
        DEBUG_JIT = _readenv("NUMBA_DEBUG_JIT", int, 0)

        # Enable debugging of front-end operation
        # (up to and including IR generation)
        DEBUG_FRONTEND = _readenv("NUMBA_DEBUG_FRONTEND", int, 0)

        # How many recently deserialized functions to retain regardless
        # of external references
        FUNCTION_CACHE_SIZE = _readenv("NUMBA_FUNCTION_CACHE_SIZE", int, 128)

        # Maximum tuple size that parfors will unpack and pass to
        # internal gufunc.
        PARFOR_MAX_TUPLE_SIZE = _readenv("NUMBA_PARFOR_MAX_TUPLE_SIZE",
                                         int, 100)

        # Enable logging of cache operation
        DEBUG_CACHE = _readenv("NUMBA_DEBUG_CACHE", int, DEBUG)

        # Redirect cache directory
        # Contains path to the directory
        CACHE_DIR = _readenv("NUMBA_CACHE_DIR", str, "")

        # Enable tracing support
        TRACE = _readenv("NUMBA_TRACE", int, 0)

        # Enable debugging of type inference
        DEBUG_TYPEINFER = _readenv("NUMBA_DEBUG_TYPEINFER", int, 0)

        # Configure compilation target to use the specified CPU name
        # and CPU feature as the host information.
        # Note: this overrides "host" option for AOT compilation.
        CPU_NAME = _readenv("NUMBA_CPU_NAME", optional_str, None)
        CPU_FEATURES = _readenv("NUMBA_CPU_FEATURES", optional_str,
                                ("" if str(CPU_NAME).lower() == 'generic'
                                 else None))
        # Optimization level
        OPT = _readenv("NUMBA_OPT", int, 3)

        # Force dump of Python bytecode
        DUMP_BYTECODE = _readenv("NUMBA_DUMP_BYTECODE", int, DEBUG_FRONTEND)

        # Force dump of control flow graph
        DUMP_CFG = _readenv("NUMBA_DUMP_CFG", int, DEBUG_FRONTEND)

        # Force dump of Numba IR
        DUMP_IR = _readenv("NUMBA_DUMP_IR", int,
                           DEBUG_FRONTEND or DEBUG_TYPEINFER)

        # print debug info of analysis and optimization on array operations
        DEBUG_ARRAY_OPT = _readenv("NUMBA_DEBUG_ARRAY_OPT", int, 0)

        # insert debug stmts to print information at runtime
        DEBUG_ARRAY_OPT_RUNTIME = _readenv(
            "NUMBA_DEBUG_ARRAY_OPT_RUNTIME", int, 0)

        # print stats about parallel for-loops
        DEBUG_ARRAY_OPT_STATS = _readenv("NUMBA_DEBUG_ARRAY_OPT_STATS", int, 0)

        # prints user friendly information about parallel
        PARALLEL_DIAGNOSTICS = _readenv("NUMBA_PARALLEL_DIAGNOSTICS", int, 0)

        # print debug info of inline closure pass
        DEBUG_INLINE_CLOSURE = _readenv("NUMBA_DEBUG_INLINE_CLOSURE", int, 0)

        # Force dump of LLVM IR
        DUMP_LLVM = _readenv("NUMBA_DUMP_LLVM", int, DEBUG)

        # Force dump of Function optimized LLVM IR
        DUMP_FUNC_OPT = _readenv("NUMBA_DUMP_FUNC_OPT", int, DEBUG)

        # Force dump of Optimized LLVM IR
        DUMP_OPTIMIZED = _readenv("NUMBA_DUMP_OPTIMIZED", int, DEBUG)

        # Force disable loop vectorize
        # Loop vectorizer is disabled on 32-bit win32 due to a bug (#649)
        LOOP_VECTORIZE = _readenv("NUMBA_LOOP_VECTORIZE", int,
                                  not (IS_WIN32 and IS_32BITS))

        # Force dump of generated assembly
        DUMP_ASSEMBLY = _readenv("NUMBA_DUMP_ASSEMBLY", int, DEBUG)

        # Force dump of type annotation
        ANNOTATE = _readenv("NUMBA_DUMP_ANNOTATION", int, 0)

        # Dump IR in such as way as to aid in "diff"ing.
        DIFF_IR = _readenv("NUMBA_DIFF_IR", int, 0)

        # Dump type annotation in html format
        def fmt_html_path(path):
            if path is None:
                return path
            else:
                return os.path.abspath(path)

        HTML = _readenv("NUMBA_DUMP_HTML", fmt_html_path, None)

        # Allow interpreter fallback so that Numba @jit decorator will never
        # fail. Use for migrating from old numba (<0.12) which supported
        # closure, and other yet-to-be-supported features.
        COMPATIBILITY_MODE = _readenv("NUMBA_COMPATIBILITY_MODE", int, 0)

        # x86-64 specific
        # Enable AVX on supported platforms where it won't degrade performance.
        def avx_default():
            if not _os_supports_avx():
                return False
            else:
                # There are various performance issues with AVX and LLVM
                # on some CPUs (list at
                # http://llvm.org/bugs/buglist.cgi?quicksearch=avx).
                # For now we'd rather disable it, since it can pessimize code
                cpu_name = ll.get_host_cpu_name()
                return cpu_name not in ('corei7-avx', 'core-avx-i',
                                        'sandybridge', 'ivybridge')

        ENABLE_AVX = _readenv("NUMBA_ENABLE_AVX", int, avx_default)

        # if set and SVML is available, it will be disabled
        # By default, it's disabled on 32-bit platforms.
        DISABLE_INTEL_SVML = _readenv(
            "NUMBA_DISABLE_INTEL_SVML", int, IS_32BITS)

        # Disable jit for debugging
        DISABLE_JIT = _readenv("NUMBA_DISABLE_JIT", int, 0)

        # choose parallel backend to use
        THREADING_LAYER = _readenv("NUMBA_THREADING_LAYER", str, 'default')

        # CUDA Configs

        # Force CUDA compute capability to a specific version
        FORCE_CUDA_CC = _readenv("NUMBA_FORCE_CUDA_CC", _parse_cc, None)

        # Disable CUDA support
        DISABLE_CUDA = _readenv("NUMBA_DISABLE_CUDA",
                                int, int(MACHINE_BITS == 32))

        # Enable CUDA simulator
        ENABLE_CUDASIM = _readenv("NUMBA_ENABLE_CUDASIM", int, 0)

        # CUDA logging level
        # Any level name from the *logging* module.  Case insensitive.
        # Defaults to CRITICAL if not set or invalid.
        # Note: This setting only applies when logging is not configured.
        #       Any existing logging configuration is preserved.
        CUDA_LOG_LEVEL = _readenv("NUMBA_CUDA_LOG_LEVEL", str, '')

        # Maximum number of pending CUDA deallocations (default: 10)
        CUDA_DEALLOCS_COUNT = _readenv("NUMBA_CUDA_MAX_PENDING_DEALLOCS_COUNT",
                                       int, 10)

        # Maximum ratio of pending CUDA deallocations to capacity (default: 0.2)
        CUDA_DEALLOCS_RATIO = _readenv("NUMBA_CUDA_MAX_PENDING_DEALLOCS_RATIO",
                                       float, 0.2)

        # HSA Configs

        # Disable HSA support
        DISABLE_HSA = _readenv("NUMBA_DISABLE_HSA", int, 0)

        # The default number of threads to use.
        NUMBA_DEFAULT_NUM_THREADS = max(1, multiprocessing.cpu_count())

        # Numba thread pool size (defaults to number of CPUs on the system).
        _NUMBA_NUM_THREADS = _readenv("NUMBA_NUM_THREADS", int,
                                      NUMBA_DEFAULT_NUM_THREADS)
        if ('NUMBA_NUM_THREADS' in globals()
                and globals()['NUMBA_NUM_THREADS'] != _NUMBA_NUM_THREADS):

            from numba.np.ufunc import parallel
            if parallel._is_initialized:
                raise RuntimeError("Cannot set NUMBA_NUM_THREADS to a "
                                   "different value once the threads have been "
                                   "launched (currently have %s, "
                                   "trying to set %s)" %
                                   (_NUMBA_NUM_THREADS,
                                    globals()['NUMBA_NUM_THREADS']))

        NUMBA_NUM_THREADS = _NUMBA_NUM_THREADS
        del _NUMBA_NUM_THREADS

        # Profiling support

        # Indicates if a profiler detected. Only VTune can be detected for now
        RUNNING_UNDER_PROFILER = 'VS_PROFILER' in os.environ

        # Enables jit events in LLVM to support profiling of dynamic code
        ENABLE_PROFILING = _readenv(
            "NUMBA_ENABLE_PROFILING", int, int(RUNNING_UNDER_PROFILER))

        # Debug Info

        # The default value for the `debug` flag
        DEBUGINFO_DEFAULT = _readenv("NUMBA_DEBUGINFO", int, ENABLE_PROFILING)
        CUDA_DEBUGINFO_DEFAULT = _readenv("NUMBA_CUDA_DEBUGINFO", int, 0)

        # gdb binary location
        GDB_BINARY = _readenv("NUMBA_GDB_BINARY", str, '/usr/bin/gdb')

        # CUDA Memory management
        CUDA_MEMORY_MANAGER = _readenv("NUMBA_CUDA_MEMORY_MANAGER", str,
                                       'default')

        # Inject the configuration values into the module globals
        for name, value in locals().copy().items():
            if name.isupper():
                globals()[name] = value