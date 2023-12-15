def vd_cli():
    vd.status(__version_info__)
    rc = -1
    try:
        rc = main_vd()
    except BrokenPipeError:
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno()) # handle broken pipe gracefully
    except visidata.ExpectedException as e:
        print('Error: ' + str(e))
    except FileNotFoundError as e:
        print(e)
        if options.debug:
            raise
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(rc)  # cleanup can be expensive with large datasets