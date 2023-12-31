  def register_bootstrap_options(cls, register):
    """Register bootstrap options.

    "Bootstrap options" are a small set of options whose values are useful when registering other
    options. Therefore we must bootstrap them early, before other options are registered, let
    alone parsed.

    Bootstrap option values can be interpolated into the config file, and can be referenced
    programatically in registration code, e.g., as register.bootstrap.pants_workdir.

    Note that regular code can also access these options as normal global-scope options. Their
    status as "bootstrap options" is only pertinent during option registration.
    """
    buildroot = get_buildroot()
    default_distdir_name = 'dist'
    default_distdir = os.path.join(buildroot, default_distdir_name)
    default_rel_distdir = '/{}/'.format(default_distdir_name)

    register('-l', '--level', choices=['trace', 'debug', 'info', 'warn'], default='info',
             recursive=True, help='Set the logging level.')
    register('-q', '--quiet', type=bool, recursive=True, daemon=False,
             help='Squelches most console output. NOTE: Some tasks default to behaving quietly: '
                  'inverting this option supports making them noisier than they would be otherwise.')

    # Not really needed in bootstrap options, but putting it here means it displays right
    # after -l and -q in help output, which is conveniently contextual.
    register('--colors', type=bool, default=sys.stdout.isatty(), recursive=True, daemon=False,
             help='Set whether log messages are displayed in color.')

    register('--pants-version', advanced=True, default=pants_version(),
             help='Use this pants version. Note Pants code only uses this to verify that you are '
                  'using the requested version, as Pants cannot dynamically change the version it '
                  'is using once the program is already running. This option is useful to set in '
                  'your pants.ini, however, and then you can grep the value to select which '
                  'version to use for setup scripts (e.g. `./pants`), runner scripts, IDE plugins, '
                  'etc. For example, the setup script we distribute at https://www.pantsbuild.org/install.html#recommended-installation '
                  'uses this value to determine which Python version to run with. You may find the '
                  'version of the pants instance you are running using -v, -V, or --version.')

    register('--pants-runtime-python-version', advanced=True,
             help='Use this Python version to run Pants. The option expects the major and minor '
                  'version, e.g. 2.7 or 3.6. Note Pants code only uses this to verify that you are '
                  'using the requested interpreter, as Pants cannot dynamically change the '
                  'interpreter it is using once the program is already running. This option is '
                  'useful to set in your pants.ini, however, and then you can grep the value to '
                  'select which interpreter to use for setup scripts (e.g. `./pants`), runner '
                  'scripts, IDE plugins, etc. For example, the setup script we distribute at '
                  'https://www.pantsbuild.org/install.html#recommended-installation uses this '
                  'value to determine which Python version to run with. Also note this does not mean '
                  'your own code must use this Python version. See '
                  'https://www.pantsbuild.org/python_readme.html#configure-the-python-version '
                  'for how to configure your code\'s compatibility.')

    register('--plugins', advanced=True, type=list, help='Load these plugins.')
    register('--plugin-cache-dir', advanced=True,
             default=os.path.join(get_pants_cachedir(), 'plugins'),
             help='Cache resolved plugin requirements here.')

    register('--backend-packages', advanced=True, type=list,
             default=['pants.backend.graph_info',
                      'pants.backend.python',
                      'pants.backend.jvm',
                      'pants.backend.native',
                      # TODO: Move into the graph_info backend.
                      'pants.rules.core',
                      'pants.backend.codegen.antlr.java',
                      'pants.backend.codegen.antlr.python',
                      'pants.backend.codegen.jaxb',
                      'pants.backend.codegen.protobuf.java',
                      'pants.backend.codegen.ragel.java',
                      'pants.backend.codegen.thrift.java',
                      'pants.backend.codegen.thrift.python',
                      'pants.backend.codegen.grpcio.python',
                      'pants.backend.codegen.wire.java',
                      'pants.backend.project_info'],
             help='Load backends from these packages that are already on the path. '
                  'Add contrib and custom backends to this list.')

    register('--pants-bootstrapdir', advanced=True, metavar='<dir>', default=get_pants_cachedir(),
             help='Use this dir for global cache.')
    register('--pants-configdir', advanced=True, metavar='<dir>', default=get_pants_configdir(),
             help='Use this dir for global config files.')
    register('--pants-workdir', advanced=True, metavar='<dir>',
             default=os.path.join(buildroot, '.pants.d'),
             help='Write intermediate output files to this dir.')
    register('--pants-supportdir', advanced=True, metavar='<dir>',
             default=os.path.join(buildroot, 'build-support'),
             help='Use support files from this dir.')
    register('--pants-distdir', advanced=True, metavar='<dir>',
             default=default_distdir,
             help='Write end-product artifacts to this dir. If you modify this path, you '
                  'should also update --build-ignore and --pants-ignore to include the '
                  'custom dist dir path as well.')
    register('--pants-subprocessdir', advanced=True, default=os.path.join(buildroot, '.pids'),
             help='The directory to use for tracking subprocess metadata, if any. This should '
                  'live outside of the dir used by `--pants-workdir` to allow for tracking '
                  'subprocesses that outlive the workdir data (e.g. `./pants server`).')
    register('--pants-config-files', advanced=True, type=list, daemon=False,
             default=[get_default_pants_config_file()], help='Paths to Pants config files.')
    # TODO: Deprecate the --pantsrc/--pantsrc-files options?  This would require being able
    # to set extra config file locations in an initial bootstrap config file.
    register('--pantsrc', advanced=True, type=bool, default=True,
             help='Use pantsrc files.')
    register('--pantsrc-files', advanced=True, type=list, metavar='<path>', daemon=False,
             default=['/etc/pantsrc', '~/.pants.rc'],
             help='Override config with values from these files. '
                  'Later files override earlier ones.')
    register('--pythonpath', advanced=True, type=list,
             help='Add these directories to PYTHONPATH to search for plugins.')
    register('--target-spec-file', type=list, dest='target_spec_files', daemon=False,
             help='Read additional specs from this file, one per line')
    register('--verify-config', type=bool, default=True, daemon=False,
             advanced=True,
             help='Verify that all config file values correspond to known options.')

    register('--build-ignore', advanced=True, type=list, fromfile=True,
             default=['.*/', default_rel_distdir, 'bower_components/',
                      'node_modules/', '*.egg-info/'],
             help='Paths to ignore when identifying BUILD files. '
                  'This does not affect any other filesystem operations. '
                  'Patterns use the gitignore pattern syntax (https://git-scm.com/docs/gitignore).')
    register('--pants-ignore', advanced=True, type=list, fromfile=True,
             default=['.*/', default_rel_distdir],
             help='Paths to ignore for all filesystem operations performed by pants '
                  '(e.g. BUILD file scanning, glob matching, etc). '
                  'Patterns use the gitignore syntax (https://git-scm.com/docs/gitignore).')
    register('--glob-expansion-failure', advanced=True,
             default=GlobMatchErrorBehavior.warn, type=GlobMatchErrorBehavior,
             help="Raise an exception if any targets declaring source files "
                  "fail to match any glob provided in the 'sources' argument.")

    register('--exclude-target-regexp', advanced=True, type=list, default=[], daemon=False,
             metavar='<regexp>', help='Exclude target roots that match these regexes.')
    register('--subproject-roots', type=list, advanced=True, fromfile=True, default=[],
             help='Paths that correspond with build roots for any subproject that this '
                  'project depends on.')
    register('--owner-of', type=list, default=[], daemon=False, fromfile=True, metavar='<path>',
             help='Select the targets that own these files. '
                  'This is the third target calculation strategy along with the --changed-* '
                  'options and specifying the targets directly. These three types of target '
                  'selection are mutually exclusive.')

    # These logging options are registered in the bootstrap phase so that plugins can log during
    # registration and not so that their values can be interpolated in configs.
    register('-d', '--logdir', advanced=True, metavar='<dir>',
             help='Write logs to files under this directory.')

    # This facilitates bootstrap-time configuration of pantsd usage such that we can
    # determine whether or not to use the Pailgun client to invoke a given pants run
    # without resorting to heavier options parsing.
    register('--enable-pantsd', advanced=True, type=bool, default=False,
             help='Enables use of the pants daemon (and implicitly, the v2 engine). (Beta)')

    # Shutdown pantsd after the current run.
    # This needs to be accessed at the same time as enable_pantsd,
    # so we register it at bootstrap time.
    register('--shutdown-pantsd-after-run', advanced=True, type=bool, default=False,
      help='Create a new pantsd server, and use it, and shut it down immediately after. '
           'If pantsd is already running, it will shut it down and spawn a new instance (Beta)')

    # These facilitate configuring the native engine.
    register('--native-engine-visualize-to', advanced=True, default=None, type=dir_option, daemon=False,
             help='A directory to write execution and rule graphs to as `dot` files. The contents '
                  'of the directory will be overwritten if any filenames collide.')
    register('--print-exception-stacktrace', advanced=True, type=bool,
             help='Print to console the full exception stack trace if encountered.')

    # BinaryUtil options.
    register('--binaries-baseurls', type=list, advanced=True,
             default=['https://binaries.pantsbuild.org'],
             help='List of URLs from which binary tools are downloaded. URLs are '
                  'searched in order until the requested path is found.')
    register('--binaries-fetch-timeout-secs', type=int, default=30, advanced=True, daemon=False,
             help='Timeout in seconds for URL reads when fetching binary tools from the '
                  'repos specified by --baseurls.')
    register('--binaries-path-by-id', type=dict, advanced=True,
             help=("Maps output of uname for a machine to a binary search path: "
                   "(sysname, id) -> (os, arch), e.g. {('darwin', '15'): ('mac', '10.11'), "
                   "('linux', 'arm32'): ('linux', 'arm32')}."))
    register('--allow-external-binary-tool-downloads', type=bool, default=True, advanced=True,
             help="If False, require BinaryTool subclasses to download their contents from urls "
                  "generated from --binaries-baseurls, even if the tool has an external url "
                  "generator. This can be necessary if using Pants in an environment which cannot "
                  "contact the wider Internet.")

    # Pants Daemon options.
    register('--pantsd-pailgun-host', advanced=True, default='127.0.0.1',
             help='The host to bind the pants nailgun server to.')
    register('--pantsd-pailgun-port', advanced=True, type=int, default=0,
             help='The port to bind the pants nailgun server to. Defaults to a random port.')
    register('--pantsd-log-dir', advanced=True, default=None,
             help='The directory to log pantsd output to.')
    register('--pantsd-invalidation-globs', advanced=True, type=list, fromfile=True, default=[],
             help='Filesystem events matching any of these globs will trigger a daemon restart.')

    # Watchman options.
    register('--watchman-version', advanced=True, default='4.9.0-pants1', help='Watchman version.')
    register('--watchman-supportdir', advanced=True, default='bin/watchman',
             help='Find watchman binaries under this dir. Used as part of the path to lookup '
                  'the binary with --binaries-baseurls and --pants-bootstrapdir.')
    register('--watchman-startup-timeout', type=float, advanced=True, default=30.0,
             help='The watchman socket timeout (in seconds) for the initial `watch-project` command. '
                  'This may need to be set higher for larger repos due to watchman startup cost.')
    register('--watchman-socket-timeout', type=float, advanced=True, default=0.1,
             help='The watchman client socket timeout in seconds. Setting this to too high a '
                  'value can negatively impact the latency of runs forked by pantsd.')
    register('--watchman-socket-path', type=str, advanced=True, default=None,
             help='The path to the watchman UNIX socket. This can be overridden if the default '
                  'absolute path length exceeds the maximum allowed by the OS.')

    # This option changes the parser behavior in a fundamental way (which currently invalidates
    # all caches), and needs to be parsed out early, so we make it a bootstrap option.
    register('--build-file-imports', choices=['allow', 'warn', 'error'], default='warn',
             advanced=True,
             help='Whether to allow import statements in BUILD files')

    register('--local-store-dir', advanced=True,
             help="Directory to use for engine's local file store.",
             # This default is also hard-coded into the engine's rust code in
             # fs::Store::default_path
             default=os.path.expanduser('~/.cache/pants/lmdb_store'))
    register('--remote-store-server', advanced=True, type=list, default=[],
             help='host:port of grpc server to use as remote execution file store.')
    register('--remote-store-thread-count', type=int, advanced=True,
             default=DEFAULT_EXECUTION_OPTIONS.remote_store_thread_count,
             help='Thread count to use for the pool that interacts with the remote file store.')
    register('--remote-execution-server', advanced=True,
             help='host:port of grpc server to use as remote execution scheduler.')
    register('--remote-store-chunk-bytes', type=int, advanced=True,
             default=DEFAULT_EXECUTION_OPTIONS.remote_store_chunk_bytes,
             help='Size in bytes of chunks transferred to/from the remote file store.')
    register('--remote-store-chunk-upload-timeout-seconds', type=int, advanced=True,
             default=DEFAULT_EXECUTION_OPTIONS.remote_store_chunk_upload_timeout_seconds,
             help='Timeout (in seconds) for uploads of individual chunks to the remote file store.')
    register('--remote-store-rpc-retries', type=int, advanced=True,
             default=DEFAULT_EXECUTION_OPTIONS.remote_store_rpc_retries,
             help='Number of times to retry any RPC to the remote store before giving up.')
    register('--remote-execution-process-cache-namespace', advanced=True,
             help="The cache namespace for remote process execution. "
                  "Bump this to invalidate every artifact's remote execution. "
                  "This is the remote execution equivalent of the legacy cache-key-gen-version "
                  "flag.")
    register('--remote-instance-name', advanced=True,
             help='Name of the remote execution instance to use. Used for routing within '
                  '--remote-execution-server and --remote-store-server.')
    register('--remote-ca-certs-path', advanced=True,
             help='Path to a PEM file containing CA certificates used for verifying secure '
                  'connections to --remote-execution-server and --remote-store-server. '
                  'If not specified, TLS will not be used.')
    register('--remote-oauth-bearer-token-path', advanced=True,
             help='Path to a file containing an oauth token to use for grpc connections to '
                  '--remote-execution-server and --remote-store-server. If not specified, no '
                  'authorization will be performed.')

    # This should eventually deprecate the RunTracker worker count, which is used for legacy cache
    # lookups via CacheSetup in TaskBase.
    register('--process-execution-parallelism', type=int, default=multiprocessing.cpu_count(),
             advanced=True,
             help='Number of concurrent processes that may be executed either locally and remotely.')
    register('--process-execution-cleanup-local-dirs', type=bool, default=True, advanced=True,
             help='Whether or not to cleanup directories used for local process execution '
                  '(primarily useful for e.g. debugging).')