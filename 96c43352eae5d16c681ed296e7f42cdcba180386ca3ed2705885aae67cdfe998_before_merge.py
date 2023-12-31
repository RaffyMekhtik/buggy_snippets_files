def install(prefix, specs, args, env, prune=False):
    # TODO: support all various ways this happens
    # Including 'nodefaults' in the channels list disables the defaults
    new_specs = []
    channel_urls = set()
    for elem in specs:
        if "::" in elem:
            channel_urls.add(elem.split("::")[0])
            new_specs.append(elem.split("::")[-1])
        else:
            new_specs.append(elem)
    specs = new_specs
    channel_urls = list(channel_urls)
    # TODO: support all various ways this happens
    # Including 'nodefaults' in the channels list disables the defaults
    channel_urls = channel_urls + [chan for chan in env.channels if chan != 'nodefaults']
    if 'nodefaults' not in env.channels:
        channel_urls.extend(context.channels)
    _channel_priority_map = prioritize_channels(channel_urls)

    channel_names = IndexedSet(Channel(url).canonical_name for url in _channel_priority_map)
    channels = IndexedSet(Channel(cn) for cn in channel_names)
    subdirs = IndexedSet(basename(url) for url in _channel_priority_map)

    solver = Solver(prefix, channels, subdirs, specs_to_add=specs)
    unlink_link_transaction = solver.solve_for_transaction(prune=prune)

    pfe = unlink_link_transaction.get_pfe()
    pfe.execute()
    unlink_link_transaction.execute()