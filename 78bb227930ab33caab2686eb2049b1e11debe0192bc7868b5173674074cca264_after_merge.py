def _find_snippet_imports(module_name, module_data, module_path, module_args, task_vars, module_compression):
    """
    Given the source of the module, convert it to a Jinja2 template to insert
    module code and return whether it's a new or old style module.
    """

    module_substyle = module_style = 'old'

    # module_style is something important to calling code (ActionBase).  It
    # determines how arguments are formatted (json vs k=v) and whether
    # a separate arguments file needs to be sent over the wire.
    # module_substyle is extra information that's useful internally.  It tells
    # us what we have to look to substitute in the module files and whether
    # we're using module replacer or ansiballz to format the module itself.
    if _is_binary(module_data):
        module_substyle = module_style = 'binary'
    elif REPLACER in module_data:
        # Do REPLACER before from ansible.module_utils because we need make sure
        # we substitute "from ansible.module_utils basic" for REPLACER
        module_style = 'new'
        module_substyle = 'python'
        module_data = module_data.replace(REPLACER, b'from ansible.module_utils.basic import *')
    elif b'from ansible.module_utils.' in module_data:
        module_style = 'new'
        module_substyle = 'python'
    elif REPLACER_WINDOWS in module_data:
        module_style = 'new'
        module_substyle = 'powershell'
    elif REPLACER_JSONARGS in module_data:
        module_style = 'new'
        module_substyle = 'jsonargs'
    elif b'WANT_JSON' in module_data:
        module_substyle = module_style = 'non_native_want_json'

    shebang = None
    # Neither old-style, non_native_want_json nor binary modules should be modified
    # except for the shebang line (Done by modify_module)
    if module_style in ('old', 'non_native_want_json', 'binary'):
        return module_data, module_style, shebang

    output = BytesIO()
    py_module_names = set()

    if module_substyle == 'python':
        params = dict(ANSIBLE_MODULE_ARGS=module_args,)
        python_repred_params = repr(json.dumps(params))

        try:
            compression_method = getattr(zipfile, module_compression)
        except AttributeError:
            display.warning(u'Bad module compression string specified: %s.  Using ZIP_STORED (no compression)' % module_compression)
            compression_method = zipfile.ZIP_STORED

        lookup_path = os.path.join(C.DEFAULT_LOCAL_TMP, 'ansiballz_cache')
        cached_module_filename = os.path.join(lookup_path, "%s-%s" % (module_name, module_compression))

        zipdata = None
        # Optimization -- don't lock if the module has already been cached
        if os.path.exists(cached_module_filename):
            display.debug('ANSIBALLZ: using cached module: %s' % cached_module_filename)
            zipdata = open(cached_module_filename, 'rb').read()
        else:
            if module_name in action_write_locks.action_write_locks:
                display.debug('ANSIBALLZ: Using lock for %s' % module_name)
                lock = action_write_locks.action_write_locks[module_name]
            else:
                # If the action plugin directly invokes the module (instead of
                # going through a strategy) then we don't have a cross-process
                # Lock specifically for this module.  Use the "unexpected
                # module" lock instead
                display.debug('ANSIBALLZ: Using generic lock for %s' % module_name)
                lock = action_write_locks.action_write_locks[None]

            display.debug('ANSIBALLZ: Acquiring lock')
            with lock:
                display.debug('ANSIBALLZ: Lock acquired: %s' % id(lock))
                # Check that no other process has created this while we were
                # waiting for the lock
                if not os.path.exists(cached_module_filename):
                    display.debug('ANSIBALLZ: Creating module')
                    # Create the module zip data
                    zipoutput = BytesIO()
                    zf = zipfile.ZipFile(zipoutput, mode='w', compression=compression_method)
                    # Note: If we need to import from release.py first,
                    # remember to catch all exceptions: https://github.com/ansible/ansible/issues/16523
                    zf.writestr('ansible/__init__.py',
                            b'from pkgutil import extend_path\n__path__=extend_path(__path__,__name__)\n__version__="' +
                            to_bytes(__version__) + b'"\n__author__="' +
                            to_bytes(__author__) + b'"\n')
                    zf.writestr('ansible/module_utils/__init__.py', b'from pkgutil import extend_path\n__path__=extend_path(__path__,__name__)\n')

                    zf.writestr('ansible_module_%s.py' % module_name, module_data)

                    py_module_cache = { ('__init__',): b'' }
                    recursive_finder(module_name, module_data, py_module_names, py_module_cache, zf)
                    zf.close()
                    zipdata = base64.b64encode(zipoutput.getvalue())

                    # Write the assembled module to a temp file (write to temp
                    # so that no one looking for the file reads a partially
                    # written file)
                    if not os.path.exists(lookup_path):
                        # Note -- if we have a global function to setup, that would
                        # be a better place to run this
                        os.makedirs(lookup_path)
                    display.debug('ANSIBALLZ: Writing module')
                    with open(cached_module_filename + '-part', 'wb') as f:
                        f.write(zipdata)

                    # Rename the file into its final position in the cache so
                    # future users of this module can read it off the
                    # filesystem instead of constructing from scratch.
                    display.debug('ANSIBALLZ: Renaming module')
                    os.rename(cached_module_filename + '-part', cached_module_filename)
                    display.debug('ANSIBALLZ: Done creating module')

            if zipdata is None:
                display.debug('ANSIBALLZ: Reading module after lock')
                # Another process wrote the file while we were waiting for
                # the write lock.  Go ahead and read the data from disk
                # instead of re-creating it.
                try:
                    zipdata = open(cached_module_filename, 'rb').read()
                except IOError:
                    raise AnsibleError('A different worker process failed to create module file.'
                    ' Look at traceback for that process for debugging information.')
        zipdata = to_text(zipdata, errors='surrogate_or_strict')

        shebang, interpreter = _get_shebang(u'/usr/bin/python', task_vars)
        if shebang is None:
            shebang = u'#!/usr/bin/python'

        # Enclose the parts of the interpreter in quotes because we're
        # substituting it into the template as a Python string
        interpreter_parts = interpreter.split(u' ')
        interpreter = u"'{0}'".format(u"', '".join(interpreter_parts))

        now=datetime.datetime.utcnow()
        output.write(to_bytes(ACTIVE_ANSIBALLZ_TEMPLATE % dict(
            zipdata=zipdata,
            ansible_module=module_name,
            params=python_repred_params,
            shebang=shebang,
            interpreter=interpreter,
            coding=ENCODING_STRING,
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=now.minute,
            second=now.second,
        )))
        module_data = output.getvalue()

    elif module_substyle == 'powershell':
        # Module replacer for jsonargs and windows
        lines = module_data.split(b'\n')
        for line in lines:
            if REPLACER_WINDOWS in line:
                ps_data = _slurp(os.path.join(_SNIPPET_PATH, "powershell.ps1"))
                output.write(ps_data)
                py_module_names.add((b'powershell',))
                continue
            output.write(line + b'\n')
        module_data = output.getvalue()

        module_args_json = to_bytes(json.dumps(module_args))
        module_data = module_data.replace(REPLACER_JSONARGS, module_args_json)

        # Powershell/winrm don't actually make use of shebang so we can
        # safely set this here.  If we let the fallback code handle this
        # it can fail in the presence of the UTF8 BOM commonly added by
        # Windows text editors
        shebang = u'#!powershell'

        # Sanity check from 1.x days.  This is currently useless as we only
        # get here if we are going to substitute powershell.ps1 into the
        # module anyway.  Leaving it for when/if we add other powershell
        # module_utils files.
        if (b'powershell',) not in py_module_names:
            raise AnsibleError("missing required import in %s: # POWERSHELL_COMMON" % module_path)

    elif module_substyle == 'jsonargs':
        module_args_json = to_bytes(json.dumps(module_args))

        # these strings could be included in a third-party module but
        # officially they were included in the 'basic' snippet for new-style
        # python modules (which has been replaced with something else in
        # ansiballz) If we remove them from jsonargs-style module replacer
        # then we can remove them everywhere.
        python_repred_args = to_bytes(repr(module_args_json))
        module_data = module_data.replace(REPLACER_VERSION, to_bytes(repr(__version__)))
        module_data = module_data.replace(REPLACER_COMPLEX, python_repred_args)
        module_data = module_data.replace(REPLACER_SELINUX, to_bytes(','.join(C.DEFAULT_SELINUX_SPECIAL_FS)))

        # The main event -- substitute the JSON args string into the module
        module_data = module_data.replace(REPLACER_JSONARGS, module_args_json)

        facility = b'syslog.' + to_bytes(task_vars.get('ansible_syslog_facility', C.DEFAULT_SYSLOG_FACILITY), errors='surrogate_or_strict')
        module_data = module_data.replace(b'syslog.LOG_USER', facility)

    return (module_data, module_style, shebang)