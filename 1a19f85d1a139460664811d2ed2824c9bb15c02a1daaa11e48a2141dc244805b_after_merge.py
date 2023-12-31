def _log_and_exit(msg: str, exc: BaseException, formatted: str) -> None:
    error_msg = f'{msg}: {type(exc).__name__}: '.encode() + force_bytes(exc)
    output.write_line_b(error_msg)
    log_path = os.path.join(Store().directory, 'pre-commit.log')
    output.write_line(f'Check the log at {log_path}')

    with open(log_path, 'wb') as log:
        _log_line = functools.partial(output.write_line, stream=log)
        _log_line_b = functools.partial(output.write_line_b, stream=log)

        _log_line('### version information')
        _log_line()
        _log_line('```')
        _log_line(f'pre-commit version: {C.VERSION}')
        _log_line('sys.version:')
        for line in sys.version.splitlines():
            _log_line(f'    {line}')
        _log_line(f'sys.executable: {sys.executable}')
        _log_line(f'os.name: {os.name}')
        _log_line(f'sys.platform: {sys.platform}')
        _log_line('```')
        _log_line()

        _log_line('### error information')
        _log_line()
        _log_line('```')
        _log_line_b(error_msg)
        _log_line('```')
        _log_line()
        _log_line('```')
        _log_line(formatted)
        _log_line('```')
    raise SystemExit(1)