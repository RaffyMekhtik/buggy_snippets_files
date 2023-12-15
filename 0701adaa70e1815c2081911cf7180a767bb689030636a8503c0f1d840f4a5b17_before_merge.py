def sort_imports(
    file_name: str,
    config: Config,
    check: bool = False,
    ask_to_apply: bool = False,
    write_to_stdout: bool = False,
    **kwargs: Any,
) -> Optional[SortAttempt]:
    incorrectly_sorted: bool = False
    skipped: bool = False
    try:
        if check:
            try:
                incorrectly_sorted = not api.check_file(file_name, config=config, **kwargs)
            except FileSkipped:
                skipped = True
            return SortAttempt(incorrectly_sorted, skipped, True)

        try:
            incorrectly_sorted = not api.sort_file(
                file_name,
                config=config,
                ask_to_apply=ask_to_apply,
                write_to_stdout=write_to_stdout,
                **kwargs,
            )
        except FileSkipped:
            skipped = True
        return SortAttempt(incorrectly_sorted, skipped, True)
    except (OSError, ValueError) as error:
        warn(f"Unable to parse file {file_name} due to {error}")
        return None
    except UnsupportedEncoding:
        if config.verbose:
            warn(f"Encoding not supported for {file_name}")
        return SortAttempt(incorrectly_sorted, skipped, False)
    except Exception:
        printer = create_terminal_printer(color=config.color_output)
        printer.error(
            f"Unrecoverable exception thrown when parsing {file_name}! "
            "This should NEVER happen.\n"
            "If encountered, please open an issue: https://github.com/PyCQA/isort/issues/new"
        )
        raise