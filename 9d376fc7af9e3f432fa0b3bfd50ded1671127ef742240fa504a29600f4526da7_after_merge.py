def main(args=None):
    if args is None:
        args = sys.argv[1:]

    options = parse_args(args)
    setup_logging(options)

    # /dev/urandom may be slow, so we cache the data first
    log.info('Preparing test data...')
    rnd_fh = tempfile.TemporaryFile()
    with open('/dev/urandom', 'rb', 0) as src:
        copied = 0
        while copied < 50 * 1024 * 1024:
            buf = src.read(BUFSIZE)
            rnd_fh.write(buf)
            copied += len(buf)

    log.info('Measuring throughput to cache...')
    backend_dir = tempfile.mkdtemp(prefix='s3ql-benchmark-')
    mnt_dir = tempfile.mkdtemp(prefix='s3ql-mnt')
    atexit.register(shutil.rmtree, backend_dir)
    atexit.register(shutil.rmtree, mnt_dir)

    block_sizes = [ 2**b for b in range(12, 18) ]
    for blocksize in block_sizes:
        write_time = 0
        size = 50 * 1024 * 1024
        while write_time < 3:
            log.debug('Write took %.3g seconds, retrying', write_time)
            subprocess.check_call([exec_prefix + 'mkfs.s3ql', '--plain', 'local://%s' % backend_dir,
                                   '--quiet', '--force', '--cachedir', options.cachedir])
            subprocess.check_call([exec_prefix + 'mount.s3ql', '--threads', '1', '--quiet',
                                   '--cachesize', '%d' % (2 * size / 1024), '--log',
                                   '%s/mount.log' % backend_dir, '--cachedir', options.cachedir,
                                   'local://%s' % backend_dir, mnt_dir])
            try:
                size *= 2
                with open('%s/bigfile' % mnt_dir, 'wb', 0) as dst:
                    rnd_fh.seek(0)
                    write_time = time.time()
                    copied = 0
                    while copied < size:
                        buf = rnd_fh.read(blocksize)
                        if not buf:
                            rnd_fh.seek(0)
                            continue
                        dst.write(buf)
                        copied += len(buf)

                write_time = time.time() - write_time
                os.unlink('%s/bigfile' % mnt_dir)
            finally:
                subprocess.check_call([exec_prefix + 'umount.s3ql', mnt_dir])

        fuse_speed = copied / write_time
        log.info('Cache throughput with %3d KiB blocks: %d KiB/sec',
                 blocksize / 1024, fuse_speed / 1024)

    # Upload random data to prevent effects of compression
    # on the network layer
    log.info('Measuring raw backend throughput..')
    try:
        backend = get_backend(options, raw=True)
    except DanglingStorageURLError as exc:
        raise QuietError(str(exc)) from None

    upload_time = 0
    size = 512 * 1024
    while upload_time < 10:
        size *= 2
        def do_write(dst):
            rnd_fh.seek(0)
            stamp = time.time()
            copied = 0
            while copied < size:
                buf = rnd_fh.read(BUFSIZE)
                if not buf:
                    rnd_fh.seek(0)
                    continue
                dst.write(buf)
                copied += len(buf)
            return (copied, stamp)
        (upload_size, upload_time) = backend.perform_write(do_write, 's3ql_testdata')
        upload_time = time.time() - upload_time
    backend_speed = upload_size / upload_time
    log.info('Backend throughput: %d KiB/sec', backend_speed / 1024)
    backend.delete('s3ql_testdata')

    src = options.file
    size = os.fstat(options.file.fileno()).st_size
    log.info('Test file size: %.2f MiB', (size / 1024 ** 2))

    in_speed = dict()
    out_speed = dict()
    for alg in ALGS:
        log.info('compressing with %s-6...', alg)
        backend = ComprencBackend(b'pass', (alg, 6),Backend(argparse.Namespace(storage_url='local://' + backend_dir)))
        def do_write(dst): #pylint: disable=E0102
            src.seek(0)
            stamp = time.time()
            while True:
                buf = src.read(BUFSIZE)
                if not buf:
                    break
                dst.write(buf)
            return (dst, stamp)
        (dst_fh, stamp) = backend.perform_write(do_write, 's3ql_testdata')
        dt = time.time() - stamp
        in_speed[alg] = size / dt
        out_speed[alg] = dst_fh.get_obj_size() / dt
        log.info('%s compression speed: %d KiB/sec per thread (in)', alg, in_speed[alg] / 1024)
        log.info('%s compression speed: %d KiB/sec per thread (out)', alg, out_speed[alg] / 1024)

    print('')
    print('With %d KiB blocks, maximum performance for different compression'
          % (block_sizes[-1]/1024), 'algorithms and thread counts is:', '', sep='\n')

    threads = set([1,2,4,8])
    cores = os.sysconf('SC_NPROCESSORS_ONLN')
    if cores != -1:
        threads.add(cores)
    if options.threads:
        threads.add(options.threads)

    print('%-26s' % 'Threads:',
          ('%12d' * len(threads)) % tuple(sorted(threads)))

    for alg in ALGS:
        speeds = []
        limits = []
        for t in sorted(threads):
            if fuse_speed > t * in_speed[alg]:
                limit = 'CPU'
                speed = t * in_speed[alg]
            else:
                limit = 'S3QL/FUSE'
                speed = fuse_speed

            if speed / in_speed[alg] * out_speed[alg] > backend_speed:
                limit = 'uplink'
                speed = backend_speed * in_speed[alg] / out_speed[alg]

            limits.append(limit)
            speeds.append(speed / 1024)

        print('%-26s' % ('Max FS throughput (%s):' % alg),
              ('%7d KiB/s' * len(threads)) % tuple(speeds))
        print('%-26s' % '..limited by:',
              ('%12s' * len(threads)) % tuple(limits))

    print('')
    print('All numbers assume that the test file is representative and that',
          'there are enough processor cores to run all active threads in parallel.',
          'To compensate for network latency, you should use about twice as',
          'many upload threads as indicated by the above table.\n', sep='\n')