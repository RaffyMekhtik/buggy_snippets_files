def __virtual__():
    '''
    Only works on Windows systems
    '''
    if salt.utils.is_windows():
        if HAS_WINDOWS_MODULES:
            global check_perms, get_managed, makedirs_perms, manage_file
            global source_list, mkdir, __clean_tmp, makedirs, file_exists
            global check_managed, check_file_meta, remove, append

            remove = _namespaced_function(remove, globals())
            append = _namespaced_function(append, globals())
            check_perms = _namespaced_function(check_perms, globals())
            get_managed = _namespaced_function(get_managed, globals())
            check_managed = _namespaced_function(check_managed, globals())
            check_file_meta = _namespaced_function(check_file_meta, globals())
            makedirs_perms = _namespaced_function(makedirs_perms, globals())
            makedirs = _namespaced_function(makedirs, globals())
            manage_file = _namespaced_function(manage_file, globals())
            source_list = _namespaced_function(source_list, globals())
            mkdir = _namespaced_function(mkdir, globals())
            file_exists = _namespaced_function(file_exists, globals())
            __clean_tmp = _namespaced_function(__clean_tmp, globals())

            return 'file'
        log.warn(salt.utils.required_modules_error(__file__, __doc__))
    return False