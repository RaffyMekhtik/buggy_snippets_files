    def __init__ (self, data, headers=None, pconfig=None):
        """ Prepare data for use in a table or plot """
        if headers is None:
            headers = []
        if pconfig is None:
            pconfig = {}

        # Given one dataset - turn it into a list
        if type(data) is not list:
            data = [data]
        if type(headers) is not list:
            headers = [headers]

        sectcols = ['55,126,184', '77,175,74', '152,78,163', '255,127,0', '228,26,28', '255,255,51', '166,86,40', '247,129,191', '153,153,153']
        shared_keys = defaultdict(lambda: dict())

        # Go through each table section
        for idx, d in enumerate(data):

            # Get the header keys
            try:
                keys = headers[idx].keys()
                assert len(keys) > 0
            except (IndexError, AttributeError, AssertionError):
                keys = list()
                for samp in d.values():
                    for k in samp.keys():
                        if k not in keys:
                            keys.append(k)
                try:
                    headers[idx]
                except IndexError:
                    headers.append(list)
                headers[idx] = OrderedDict()
                for k in keys:
                    headers[idx][k] = {}

            # Ensure that keys are strings, not numeric
            keys = [str(k) for k in keys]
            for k in list(headers[idx].keys()):
                headers[idx][str(k)] = headers[idx].pop(k)
            for s_name in data[idx].keys():
                for k in list(data[idx][s_name].keys()):
                    data[idx][s_name][str(k)] = data[idx][s_name].pop(k)

            # Check that we have some data in each column
            empties = list()
            for k in keys:
                n = 0
                for samp in d.values():
                    if k in samp:
                        n += 1
                if n == 0:
                    empties.append(k)
            for k in empties:
                keys = [j for j in keys if j != k]
                del headers[idx][k]

            for k in keys:
                # Unique id to avoid overwriting by other datasets
                headers[idx][k]['rid'] = '{}_{}'.format( id(headers[idx]), re.sub(r'\W+', '_', k) )

                # Use defaults / data keys if headers not given
                headers[idx][k]['namespace']   = headers[idx][k].get('namespace', pconfig.get('namespace', ''))
                headers[idx][k]['title']       = headers[idx][k].get('title', k)
                headers[idx][k]['description'] = headers[idx][k].get('description', headers[idx][k]['title'])
                headers[idx][k]['scale']       = headers[idx][k].get('scale', pconfig.get('scale', 'GnBu'))
                headers[idx][k]['format']      = headers[idx][k].get('format', pconfig.get('format', '{:,.1f}'))
                headers[idx][k]['colour']      = headers[idx][k].get('colour', pconfig.get('colour', None))
                headers[idx][k]['hidden']      = headers[idx][k].get('hidden', pconfig.get('hidden', None))
                headers[idx][k]['max']         = headers[idx][k].get('max', pconfig.get('max', None))
                headers[idx][k]['min']         = headers[idx][k].get('min', pconfig.get('min', None))
                headers[idx][k]['ceiling']     = headers[idx][k].get('ceiling', pconfig.get('ceiling', None))
                headers[idx][k]['floor']       = headers[idx][k].get('floor', pconfig.get('floor', None))
                headers[idx][k]['minRange']    = headers[idx][k].get('minRange', pconfig.get('minRange', None))
                headers[idx][k]['shared_key']  = headers[idx][k].get('shared_key', pconfig.get('shared_key', None))
                headers[idx][k]['modify']      = headers[idx][k].get('modify', pconfig.get('modify', None))
                headers[idx][k]['placement']   = float( headers[idx][k].get('placement', 1000) )

                if headers[idx][k]['colour'] is None:
                    cidx = idx
                    while cidx >= len(sectcols):
                        cidx -= len(sectcols)
                    headers[idx][k]['colour'] = sectcols[cidx]

                # Overwrite hidden if set in user config
                try:
                    # Config has True = visibile, False = Hidden. Here we're setting "hidden" which is inverse
                    headers[idx][k]['hidden'] = not config.table_columns_visible[ headers[idx][k]['namespace'] ][k]
                except KeyError:
                    pass

                # Also overwite placement if set in config
                try:
                    headers[idx][k]['placement'] = float(config.table_columns_placement[ headers[idx][k]['namespace'] ][k])
                except (KeyError, ValueError):
                    pass

                # Work out max and min value if not given
                setdmax = False
                setdmin = False
                try:
                    headers[idx][k]['dmax'] = float(headers[idx][k]['max'])
                except TypeError:
                    headers[idx][k]['dmax'] = 0
                    setdmax = True

                try:
                    headers[idx][k]['dmin'] = float(headers[idx][k]['min'])
                except TypeError:
                    headers[idx][k]['dmin'] = 0
                    setdmin = True

                # Figure out the min / max if not supplied
                if setdmax or setdmin:
                    for s_name, samp in data[idx].items():
                        try:
                            val = float(samp[k])
                            if callable(headers[idx][k]['modify']):
                                val = float(headers[idx][k]['modify'](val))
                            if setdmax:
                                headers[idx][k]['dmax'] = max(headers[idx][k]['dmax'], val)
                            if setdmin:
                                headers[idx][k]['dmin'] = min(headers[idx][k]['dmin'], val)
                        except ValueError:
                            val = samp[k] # couldn't convert to float - keep as a string
                        except KeyError:
                            pass # missing data - skip
                    # Limit auto-generated scales with floor, ceiling and minRange.
                    if headers[idx][k]['ceiling'] is not None and headers[idx][k]['max'] is None:
                        headers[idx][k]['dmax'] = min(headers[idx][k]['dmax'], float(headers[idx][k]['ceiling']))
                    if headers[idx][k]['floor'] is not None and headers[idx][k]['min'] is None:
                        headers[idx][k]['dmin'] = max(headers[idx][k]['dmin'], float(headers[idx][k]['floor']))
                    if headers[idx][k]['minRange'] is not None:
                        drange = headers[idx][k]['dmax'] - headers[idx][k]['dmin']
                        if drange < float(headers[idx][k]['minRange']):
                            headers[idx][k]['dmax'] = headers[idx][k]['dmin'] + float(headers[idx][k]['minRange'])

        # Collect settings for shared keys
        shared_keys = defaultdict(lambda: dict())
        for idx, hs in enumerate(headers):
            for k in hs.keys():
                sk = headers[idx][k]['shared_key']
                if sk is not None:
                    shared_keys[sk]['dmax']  = max(headers[idx][k]['dmax'], shared_keys[sk].get('dmax', headers[idx][k]['dmax']))
                    shared_keys[sk]['dmin']  = max(headers[idx][k]['dmin'], shared_keys[sk].get('dmin', headers[idx][k]['dmin']))

        # Overwrite shared key settings and at the same time assign to buckets for sorting
        # Within each section of headers, sort explicitly by 'title' if the dict
        # is not already ordered, so the final ordering is by:
        # placement > section > explicit_ordering > title
        # Of course, the user can shuffle these manually.
        self.headers_in_order = defaultdict(list)

        for idx, hs in enumerate(headers):
            keys_in_section = hs.keys()
            if type(hs) is not OrderedDict:
                keys_in_section = sorted(keys_in_section, key=lambda k: headers[idx][k]['title'])

            for k in keys_in_section:
                sk = headers[idx][k]['shared_key']
                if sk is not None:
                    headers[idx][k]['dmax'] = shared_keys[sk]['dmax']
                    headers[idx][k]['dmin'] = shared_keys[sk]['dmin']

                self.headers_in_order[headers[idx][k]['placement']].append((idx, k))

        # Assign to class
        self.data = data
        self.headers = headers
        self.pconfig = pconfig