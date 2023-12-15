    def create_one_client(self):
        """
        Creates an XMLPRC client to OpenNebula.

        Returns: the new xmlrpc client.

        """

        # context required for not validating SSL, old python versions won't validate anyway.
        if hasattr(ssl, '_create_unverified_context'):
            no_ssl_validation_context = ssl._create_unverified_context()
        else:
            no_ssl_validation_context = None

        # Check if the module can run
        if not HAS_PYONE:
            self.fail("pyone is required for this module")

        if 'api_url' in self.module.params:
            url = self.module.params.get("api_url", environ.get("ONE_URL", False))
        else:
            self.fail("Either api_url or the environment variable ONE_URL must be provided")

        if 'api_username' in self.module.params:
            username = self.module.params.get("api_username", environ.get("ONE_USERNAME", False))
        else:
            self.fail("Either api_username or the environment vairable ONE_USERNAME must be provided")

        if 'api_password' in self.module.params:
            password = self.module.params.get("api_password", environ.get("ONE_PASSWORD", False))
        else:
            self.fail("Either api_password or the environment vairable ONE_PASSWORD must be provided")

        session = "%s:%s" % (username, password)

        if not self.module.params.get("validate_certs") and "PYTHONHTTPSVERIFY" not in environ:
            return OneServer(url, session=session, context=no_ssl_validation_context)
        else:
            return OneServer(url, session)