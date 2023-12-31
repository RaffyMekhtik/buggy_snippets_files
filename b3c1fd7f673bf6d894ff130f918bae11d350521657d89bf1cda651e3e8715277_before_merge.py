    def run(self):
        '''
        Execute the salt-cloud command line
        '''
        # Parse shell arguments
        self.parse_args()

        salt_master_user = self.config.get('user', salt.utils.get_user())
        if salt_master_user is not None and not check_user(salt_master_user):
            self.error(
                'If salt-cloud is running on a master machine, salt-cloud '
                'needs to run as the same user as the salt-master, {0!r}. If '
                'salt-cloud is not running on a salt-master, the appropriate '
                'write permissions must be granted to /etc/salt/. Please run '
                'salt-cloud as root, {0!r}, or change permissions for '
                '/etc/salt/.'.format(salt_master_user)
            )

        try:
            if self.config['verify_env']:
                verify_env(
                    [os.path.dirname(self.config['conf_file'])],
                    salt_master_user
                )
                logfile = self.config['log_file']
                if logfile is not None and not logfile.startswith('tcp://') \
                        and not logfile.startswith('udp://') \
                        and not logfile.startswith('file://'):
                    # Logfile is not using Syslog, verify
                    verify_files([logfile], salt_master_user)
        except (IOError, OSError) as err:
            log.error('Error while verifying the environment: {0}'.format(err))
            sys.exit(err.errno)

        # Setup log file logging
        self.setup_logfile_logger()

        if self.options.update_bootstrap:
            ret = salt.utils.cloud.update_bootstrap(self.config)
            display_output = salt.output.get_printout(
                self.options.output, self.config
            )
            print(display_output(ret))
            self.exit(salt.defaults.exitcodes.EX_OK)

        log.info('salt-cloud starting')
        mapper = salt.cloud.Map(self.config)

        names = self.config.get('names', None)
        if names is not None:
            filtered_rendered_map = {}
            for map_profile in mapper.rendered_map:
                filtered_map_profile = {}
                for name in mapper.rendered_map[map_profile]:
                    if name in names:
                        filtered_map_profile[name] = mapper.rendered_map[map_profile][name]
                if filtered_map_profile:
                    filtered_rendered_map[map_profile] = filtered_map_profile
            mapper.rendered_map = filtered_rendered_map

        ret = {}

        if self.selected_query_option is not None:
            if self.selected_query_option == 'list_providers':
                try:
                    ret = mapper.provider_list()
                except (SaltCloudException, Exception) as exc:
                    msg = 'There was an error listing providers: {0}'
                    self.handle_exception(msg, exc)

            elif self.selected_query_option == 'list_profiles':
                provider = self.options.list_profiles
                try:
                    ret = mapper.profile_list(provider)
                except(SaltCloudException, Exception) as exc:
                    msg = 'There was an error listing profiles: {0}'
                    self.handle_exception(msg, exc)

            elif self.config.get('map', None):
                log.info('Applying map from {0!r}.'.format(self.config['map']))
                try:
                    ret = mapper.interpolated_map(
                        query=self.selected_query_option
                    )
                except (SaltCloudException, Exception) as exc:
                    msg = 'There was an error with a custom map: {0}'
                    self.handle_exception(msg, exc)
            else:
                try:
                    ret = mapper.map_providers_parallel(
                        query=self.selected_query_option
                    )
                except (SaltCloudException, Exception) as exc:
                    msg = 'There was an error with a map: {0}'
                    self.handle_exception(msg, exc)

        elif self.options.list_locations is not None:
            try:
                ret = mapper.location_list(
                    self.options.list_locations
                )
            except (SaltCloudException, Exception) as exc:
                msg = 'There was an error listing locations: {0}'
                self.handle_exception(msg, exc)

        elif self.options.list_images is not None:
            try:
                ret = mapper.image_list(
                    self.options.list_images
                )
            except (SaltCloudException, Exception) as exc:
                msg = 'There was an error listing images: {0}'
                self.handle_exception(msg, exc)

        elif self.options.list_sizes is not None:
            try:
                ret = mapper.size_list(
                    self.options.list_sizes
                )
            except (SaltCloudException, Exception) as exc:
                msg = 'There was an error listing sizes: {0}'
                self.handle_exception(msg, exc)

        elif self.options.destroy and (self.config.get('names', None) or
                                       self.config.get('map', None)):
            if self.config.get('map', None):
                log.info('Applying map from {0!r}.'.format(self.config['map']))
                matching = mapper.delete_map(query='list_nodes')
            else:
                matching = mapper.get_running_by_names(
                    self.config.get('names', ()),
                    profile=self.options.profile
                )

            if not matching:
                print('No machines were found to be destroyed')
                self.exit(salt.defaults.exitcodes.EX_OK)

            msg = 'The following virtual machines are set to be destroyed:\n'
            names = set()
            for alias, drivers in six.iteritems(matching):
                msg += '  {0}:\n'.format(alias)
                for driver, vms in six.iteritems(drivers):
                    msg += '    {0}:\n'.format(driver)
                    for name in vms:
                        msg += '      {0}\n'.format(name)
                        names.add(name)
            try:
                if self.print_confirm(msg):
                    ret = mapper.destroy(names, cached=True)
            except (SaltCloudException, Exception) as exc:
                msg = 'There was an error destroying machines: {0}'
                self.handle_exception(msg, exc)

        elif self.options.action and (self.config.get('names', None) or
                                      self.config.get('map', None)):
            if self.config.get('map', None):
                log.info('Applying map from {0!r}.'.format(self.config['map']))
                names = mapper.get_vmnames_by_action(self.options.action)
            else:
                names = self.config.get('names', None)

            kwargs = {}
            machines = []
            msg = (
                'The following virtual machines are set to be actioned with '
                '"{0}":\n'.format(
                    self.options.action
                )
            )
            for name in names:
                if '=' in name:
                    # This is obviously not a machine name, treat it as a kwarg
                    comps = name.split('=')
                    kwargs[comps[0]] = comps[1]
                else:
                    msg += '  {0}\n'.format(name)
                    machines.append(name)
            names = machines

            try:
                if self.print_confirm(msg):
                    ret = mapper.do_action(names, kwargs)
            except (SaltCloudException, Exception) as exc:
                msg = 'There was an error actioning machines: {0}'
                self.handle_exception(msg, exc)

        elif self.options.function:
            kwargs = {}
            args = self.args[:]
            for arg in args[:]:
                if '=' in arg:
                    key, value = arg.split('=')
                    kwargs[key] = value
                    args.remove(arg)

            if args:
                self.error(
                    'Any arguments passed to --function need to be passed '
                    'as kwargs. Ex: image=ami-54cf5c3d. Remaining '
                    'arguments: {0}'.format(args)
                )
            try:
                ret = mapper.do_function(
                    self.function_provider, self.function_name, kwargs
                )
            except (SaltCloudException, Exception) as exc:
                msg = 'There was an error running the function: {0}'
                self.handle_exception(msg, exc)

        elif self.options.profile and self.config.get('names', False):
            try:
                ret = mapper.run_profile(
                    self.options.profile,
                    self.config.get('names')
                )
            except (SaltCloudException, Exception) as exc:
                msg = 'There was a profile error: {0}'
                self.handle_exception(msg, exc)

        elif self.options.set_password:
            username = self.credential_username
            provider_name = "salt.cloud.provider.{0}".format(self.credential_provider)
            # TODO: check if provider is configured
            # set the password
            salt.utils.cloud.store_password_in_keyring(provider_name, username)
        elif self.config.get('map', None) and \
                self.selected_query_option is None:
            if len(mapper.rendered_map) == 0:
                sys.stderr.write('No nodes defined in this map')
                self.exit(salt.defaults.exitcodes.EX_GENERIC)
            try:
                ret = {}
                run_map = True

                log.info('Applying map from {0!r}.'.format(self.config['map']))
                dmap = mapper.map_data()

                msg = ''
                if 'errors' in dmap:
                    # display profile errors
                    msg += 'Found the following errors:\n'
                    for profile_name, error in six.iteritems(dmap['errors']):
                        msg += '  {0}: {1}\n'.format(profile_name, error)
                    sys.stderr.write(msg)
                    sys.stderr.flush()

                msg = ''
                if 'existing' in dmap:
                    msg += ('The following virtual machines already exist:\n')
                    for name in dmap['existing']:
                        msg += '  {0}\n'.format(name)

                if dmap['create']:
                    msg += ('The following virtual machines are set to be '
                            'created:\n')
                    for name in dmap['create']:
                        msg += '  {0}\n'.format(name)

                if 'destroy' in dmap:
                    msg += ('The following virtual machines are set to be '
                            'destroyed:\n')
                    for name in dmap['destroy']:
                        msg += '  {0}\n'.format(name)

                if not dmap['create'] and not dmap.get('destroy', None):
                    if not dmap.get('existing', None):
                        # nothing to create or destroy & nothing exists
                        print(msg)
                        self.exit(1)
                    else:
                        # nothing to create or destroy, print existing
                        run_map = False

                if run_map:
                    if self.print_confirm(msg):
                        ret = mapper.run_map(dmap)

                    if self.config.get('parallel', False) is False:
                        log.info('Complete')

                if dmap.get('existing', None):
                    for name in dmap['existing']:
                        ret[name] = {'Message': 'Already running'}

            except (SaltCloudException, Exception) as exc:
                msg = 'There was a query error: {0}'
                self.handle_exception(msg, exc)

        else:
            self.error('Nothing was done. Using the proper arguments?')

        display_output = salt.output.get_printout(
            self.options.output, self.config
        )
        # display output using salt's outputter system
        print(display_output(ret))
        self.exit(salt.defaults.exitcodes.EX_OK)