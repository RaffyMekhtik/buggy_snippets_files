    def sign_in(self, timeout=60, safe=True, tries=1):
        '''
        Send a sign in request to the master, sets the key information and
        returns a dict containing the master publish interface to bind to
        and the decrypted aes key for transport decryption.

        :param int timeout: Number of seconds to wait before timing out the sign-in request
        :param bool safe: If True, do not raise an exception on timeout. Retry instead.
        :param int tries: The number of times to try to authenticate before giving up.

        :raises SaltReqTimeoutError: If the sign-in request has timed out and :param safe: is not set

        :return: Return a string on failure indicating the reason for failure. On success, return a dictionary
        with the publication port and the shared AES key.

        '''
        auth = {}

        auth_timeout = self.opts.get('auth_timeout', None)
        if auth_timeout is not None:
            timeout = auth_timeout
        auth_safemode = self.opts.get('auth_safemode', None)
        if auth_safemode is not None:
            safe = auth_safemode
        auth_tries = self.opts.get('auth_tries', None)
        if auth_tries is not None:
            tries = auth_tries

        m_pub_fn = os.path.join(self.opts['pki_dir'], self.mpub)

        auth['master_uri'] = self.opts['master_uri']

        channel = salt.transport.client.ReqChannel.factory(self.opts, crypt='clear')

        try:
            payload = channel.send(
                self.minion_sign_in_payload(),
                tries=tries,
                timeout=timeout
            )
        except SaltReqTimeoutError as e:
            if safe:
                log.warning('SaltReqTimeoutError: {0}'.format(e))
                return 'retry'
            raise SaltClientError('Attempt to authenticate with the salt master failed')

        if 'load' in payload:
            if 'ret' in payload['load']:
                if not payload['load']['ret']:
                    if self.opts['rejected_retry']:
                        log.error(
                            'The Salt Master has rejected this minion\'s public '
                            'key.\nTo repair this issue, delete the public key '
                            'for this minion on the Salt Master.\nThe Salt '
                            'Minion will attempt to to re-authenicate.'
                        )
                        return 'retry'
                    else:
                        log.critical(
                            'The Salt Master has rejected this minion\'s public '
                            'key!\nTo repair this issue, delete the public key '
                            'for this minion on the Salt Master and restart this '
                            'minion.\nOr restart the Salt Master in open mode to '
                            'clean out the keys. The Salt Minion will now exit.'
                        )
                        sys.exit(salt.defaults.exitcodes.EX_OK)
                # has the master returned that its maxed out with minions?
                elif payload['load']['ret'] == 'full':
                    return 'full'
                else:
                    log.error(
                        'The Salt Master has cached the public key for this '
                        'node. If this is the first time connecting to this master '
                        'then this key may need to be accepted using \'salt-key -a {0}\' on '
                        'the salt master. This salt minion will wait for {1} seconds '
                        'before attempting to re-authenticate.'.format(
                            self.opts['id'],
                            self.opts['acceptance_wait_time']
                        )
                    )
                    return 'retry'
        auth['aes'] = self.verify_master(payload)
        if not auth['aes']:
            log.critical(
                'The Salt Master server\'s public key did not authenticate!\n'
                'The master may need to be updated if it is a version of Salt '
                'lower than {0}, or\n'
                'If you are confident that you are connecting to a valid Salt '
                'Master, then remove the master public key and restart the '
                'Salt Minion.\nThe master public key can be found '
                'at:\n{1}'.format(salt.version.__version__, m_pub_fn)
            )
            sys.exit(42)
        if self.opts.get('syndic_master', False):  # Is syndic
            syndic_finger = self.opts.get('syndic_finger', self.opts.get('master_finger', False))
            if syndic_finger:
                if salt.utils.pem_finger(m_pub_fn, sum_type=self.opts['hash_type']) != syndic_finger:
                    self._finger_fail(syndic_finger, m_pub_fn)
        else:
            if self.opts.get('master_finger', False):
                if salt.utils.pem_finger(m_pub_fn, sum_type=self.opts['hash_type']) != self.opts['master_finger']:
                    self._finger_fail(self.opts['master_finger'], m_pub_fn)
        auth['publish_port'] = payload['publish_port']
        return auth