def _locate(path: str) -> Union[type, Callable[..., Any]]:
    """
    Locate an object by name or dotted path, importing as necessary.
    This is similar to the pydoc function `locate`, except that it checks for
    the module from the given path from back to front.
    """
    if path == "":
        raise ImportError("Empty path")
    import builtins
    from importlib import import_module

    parts = [part for part in path.split(".") if part]
    module = None
    for n in reversed(range(len(parts))):
        try:
            mod = ".".join(parts[:n])
            module = import_module(mod)
        except Exception as e:
            if n == 0:
                raise ImportError(f"Error loading module '{path}'") from e
            continue
        if module:
            break
    if module:
        obj = module
    else:
        obj = builtins
    for part in parts[n:]:
        mod = mod + "." + part
        if not hasattr(obj, part):
            try:
                import_module(mod)
            except Exception as e:
                raise ImportError(
                    f"Encountered error: `{e}` when loading module '{path}'"
                ) from e
        obj = getattr(obj, part)
    if isinstance(obj, type):
        obj_type: type = obj
        return obj_type
    elif callable(obj):
        obj_callable: Callable[..., Any] = obj
        return obj_callable
    else:
        # dummy case
        raise ValueError(f"Invalid type ({type(obj)}) found for {path}")