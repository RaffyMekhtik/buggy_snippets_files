def execute_config(args, parser):
    stdout_write = getLogger("conda.stdout").info
    stderr_write = getLogger("conda.stderr").info
    json_warnings = []
    json_get = {}

    if args.show_sources:
        if context.json:
            stdout_write(
                json.dumps(context.collect_all(), sort_keys=True, indent=2, separators=(',', ': '))
            )
        else:
            lines = []
            for source, reprs in iteritems(context.collect_all()):
                lines.append("==> %s <==" % source)
                lines.extend(format_dict(reprs))
                lines.append('')
            stdout_write('\n'.join(lines))
        return

    if args.show is not None:
        if args.show:
            paramater_names = args.show
            all_names = context.list_parameters()
            not_params = set(paramater_names) - set(all_names)
            if not_params:
                from ..exceptions import ArgumentError
                from ..common.io import dashlist
                raise ArgumentError("Invalid configuration parameters: %s" % dashlist(not_params))
        else:
            paramater_names = context.list_parameters()

        d = OrderedDict((key, getattr(context, key)) for key in paramater_names)
        if context.json:
            stdout_write(json.dumps(
                d, sort_keys=True, indent=2, separators=(',', ': '), cls=EntityEncoder
            ))
        else:
            # Add in custom formatting
            if 'custom_channels' in d:
                d['custom_channels'] = {
                    channel.name: "%s://%s" % (channel.scheme, channel.location)
                    for channel in itervalues(d['custom_channels'])
                }
            if 'custom_multichannels' in d:
                from ..common.io import dashlist
                d['custom_multichannels'] = {
                    multichannel_name: dashlist(channels, indent=4)
                    for multichannel_name, channels in iteritems(d['custom_multichannels'])
                }

            stdout_write('\n'.join(format_dict(d)))
        context.validate_configuration()
        return

    if args.describe is not None:
        if args.describe:
            paramater_names = args.describe
            all_names = context.list_parameters()
            not_params = set(paramater_names) - set(all_names)
            if not_params:
                from ..exceptions import ArgumentError
                from ..common.io import dashlist
                raise ArgumentError("Invalid configuration parameters: %s" % dashlist(not_params))
            if context.json:
                stdout_write(json.dumps(
                    [context.describe_parameter(name) for name in paramater_names],
                    sort_keys=True, indent=2, separators=(',', ': '), cls=EntityEncoder
                ))
            else:
                builder = []
                builder.extend(concat(parameter_description_builder(name)
                                      for name in paramater_names))
                stdout_write('\n'.join(builder))
        else:
            if context.json:
                skip_categories = ('CLI-only', 'Hidden and Undocumented')
                paramater_names = sorted(concat(
                    parameter_names for category, parameter_names in context.category_map.items()
                    if category not in skip_categories
                ))
                stdout_write(json.dumps(
                    [context.describe_parameter(name) for name in paramater_names],
                    sort_keys=True, indent=2, separators=(',', ': '), cls=EntityEncoder
                ))
            else:
                stdout_write(describe_all_parameters())
        return

    if args.validate:
        context.validate_all()
        return

    if args.system:
        rc_path = sys_rc_path
    elif args.env:
        if 'CONDA_PREFIX' in os.environ:
            rc_path = join(os.environ['CONDA_PREFIX'], '.condarc')
        else:
            rc_path = user_rc_path
    elif args.file:
        rc_path = args.file
    else:
        rc_path = user_rc_path

    if args.write_default:
        if isfile(rc_path):
            with open(rc_path) as fh:
                data = fh.read().strip()
            if data:
                raise CondaError("The file '%s' "
                                 "already contains configuration information.\n"
                                 "Remove the file to proceed.\n"
                                 "Use `conda config --describe` to display default configuration."
                                 % rc_path)

        with open(rc_path, 'w') as fh:
            fh.write(describe_all_parameters())
        return

    # read existing condarc
    if os.path.exists(rc_path):
        with open(rc_path, 'r') as fh:
            rc_config = yaml_load(fh) or {}
    else:
        rc_config = {}

    grouped_paramaters = groupby(lambda p: context.describe_parameter(p)['parameter_type'],
                                 context.list_parameters())
    primitive_parameters = grouped_paramaters['primitive']
    sequence_parameters = grouped_paramaters['sequence']
    map_parameters = grouped_paramaters['map']

    # Get
    if args.get is not None:
        context.validate_all()
        if args.get == []:
            args.get = sorted(rc_config.keys())
        for key in args.get:
            if key not in primitive_parameters + sequence_parameters:
                message = "unknown key %s" % key
                if not context.json:
                    stderr_write(message)
                else:
                    json_warnings.append(message)
                continue
            if key not in rc_config:
                continue

            if context.json:
                json_get[key] = rc_config[key]
                continue

            if isinstance(rc_config[key], (bool, string_types)):
                stdout_write(" ".join(("--set", key, text_type(rc_config[key]))))
            else:  # assume the key is a list-type
                # Note, since conda config --add prepends, these are printed in
                # the reverse order so that entering them in this order will
                # recreate the same file
                items = rc_config.get(key, [])
                numitems = len(items)
                for q, item in enumerate(reversed(items)):
                    # Use repr so that it can be pasted back in to conda config --add
                    if key == "channels" and q in (0, numitems-1):
                        stdout_write(" ".join((
                            "--add", key, repr(item),
                            "  # lowest priority" if q == 0 else "  # highest priority"
                        )))
                    else:
                        stdout_write(" ".join(("--add", key, repr(item))))

    if args.stdin:
        content = timeout(5, sys.stdin.read)
        if not content:
            return
        try:
            parsed = yaml_load(content)
            rc_config.update(parsed)
        except Exception:  # pragma: no cover
            from ..exceptions import ParseError
            raise ParseError("invalid yaml content:\n%s" % content)

    # prepend, append, add
    for arg, prepend in zip((args.prepend, args.append), (True, False)):
        for key, item in arg:
            if key == 'channels' and key not in rc_config:
                rc_config[key] = ['defaults']
            if key not in sequence_parameters:
                from ..exceptions import CondaValueError
                raise CondaValueError("Key '%s' is not a known sequence parameter." % key)
            if not (isinstance(rc_config.get(key, []), Sequence) and not
                    isinstance(rc_config.get(key, []), string_types)):
                from ..exceptions import CouldntParseError
                bad = rc_config[key].__class__.__name__
                raise CouldntParseError("key %r should be a list, not %s." % (key, bad))
            arglist = rc_config.setdefault(key, [])
            if item in arglist:
                # Right now, all list keys should not contain duplicates
                message = "Warning: '%s' already in '%s' list, moving to the %s" % (
                    item, key, "top" if prepend else "bottom")
                arglist = rc_config[key] = [p for p in arglist if p != item]
                if not context.json:
                    stderr_write(message)
                else:
                    json_warnings.append(message)
            arglist.insert(0 if prepend else len(arglist), item)

    # Set
    for key, item in args.set:
        key, subkey = key.split('.', 1) if '.' in key else (key, None)
        if key in primitive_parameters:
            value = context.typify_parameter(key, item)
            rc_config[key] = value
        elif key in map_parameters:
            argmap = rc_config.setdefault(key, {})
            argmap[subkey] = item
        else:
            from ..exceptions import CondaValueError
            raise CondaValueError("Key '%s' is not a known primitive parameter." % key)

    # Remove
    for key, item in args.remove:
        key, subkey = key.split('.', 1) if '.' in key else (key, None)
        if key not in rc_config:
            if key != 'channels':
                from ..exceptions import CondaKeyError
                raise CondaKeyError(key, "key %r is not in the config file" % key)
            rc_config[key] = ['defaults']
        if item not in rc_config[key]:
            from ..exceptions import CondaKeyError
            raise CondaKeyError(key, "%r is not in the %r key of the config file" %
                                (item, key))
        rc_config[key] = [i for i in rc_config[key] if i != item]

    # Remove Key
    for key, in args.remove_key:
        key, subkey = key.split('.', 1) if '.' in key else (key, None)
        if key not in rc_config:
            from ..exceptions import CondaKeyError
            raise CondaKeyError(key, "key %r is not in the config file" %
                                key)
        del rc_config[key]

    # config.rc_keys
    if not args.get:

        # Add representers for enums.
        # Because a representer cannot be added for the base Enum class (it must be added for
        # each specific Enum subclass), and because of import rules), I don't know of a better
        # location to do this.
        def enum_representer(dumper, data):
            return dumper.represent_str(str(data))

        yaml.representer.RoundTripRepresenter.add_representer(SafetyChecks, enum_representer)
        yaml.representer.RoundTripRepresenter.add_representer(PathConflict, enum_representer)
        yaml.representer.RoundTripRepresenter.add_representer(DepsModifier, enum_representer)
        yaml.representer.RoundTripRepresenter.add_representer(UpdateModifier, enum_representer)
        yaml.representer.RoundTripRepresenter.add_representer(ChannelPriority, enum_representer)

        try:
            with open(rc_path, 'w') as rc:
                rc.write(yaml_dump(rc_config))
        except (IOError, OSError) as e:
            raise CondaError('Cannot write to condarc file at %s\n'
                             'Caused by %r' % (rc_path, e))

    if context.json:
        from .common import stdout_json_success
        stdout_json_success(
            rc_path=rc_path,
            warnings=json_warnings,
            get=json_get
        )
    return