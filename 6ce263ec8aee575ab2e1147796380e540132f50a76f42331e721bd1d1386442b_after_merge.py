    def read_config(self, config, config_dir_path, **kwargs):

        acme_config = config.get("acme", None)
        if acme_config is None:
            acme_config = {}

        self.acme_enabled = acme_config.get("enabled", False)

        # hyperlink complains on py2 if this is not a Unicode
        self.acme_url = six.text_type(
            acme_config.get("url", "https://acme-v01.api.letsencrypt.org/directory")
        )
        self.acme_port = acme_config.get("port", 80)
        self.acme_bind_addresses = acme_config.get("bind_addresses", ["::", "0.0.0.0"])
        self.acme_reprovision_threshold = acme_config.get("reprovision_threshold", 30)
        self.acme_domain = acme_config.get("domain", config.get("server_name"))

        self.acme_account_key_file = self.abspath(
            acme_config.get("account_key_file", config_dir_path + "/client.key")
        )

        self.tls_certificate_file = self.abspath(config.get("tls_certificate_path"))
        self.tls_private_key_file = self.abspath(config.get("tls_private_key_path"))

        if self.has_tls_listener():
            if not self.tls_certificate_file:
                raise ConfigError(
                    "tls_certificate_path must be specified if TLS-enabled listeners are "
                    "configured."
                )
            if not self.tls_private_key_file:
                raise ConfigError(
                    "tls_private_key_path must be specified if TLS-enabled listeners are "
                    "configured."
                )

        self._original_tls_fingerprints = config.get("tls_fingerprints", [])

        if self._original_tls_fingerprints is None:
            self._original_tls_fingerprints = []

        self.tls_fingerprints = list(self._original_tls_fingerprints)

        # Whether to verify certificates on outbound federation traffic
        self.federation_verify_certificates = config.get(
            "federation_verify_certificates", True
        )

        # Minimum TLS version to use for outbound federation traffic
        self.federation_client_minimum_tls_version = str(
            config.get("federation_client_minimum_tls_version", 1)
        )

        if self.federation_client_minimum_tls_version not in ["1", "1.1", "1.2", "1.3"]:
            raise ConfigError(
                "federation_client_minimum_tls_version must be one of: 1, 1.1, 1.2, 1.3"
            )

        # Prevent people shooting themselves in the foot here by setting it to
        # the biggest number blindly
        if self.federation_client_minimum_tls_version == "1.3":
            if getattr(SSL, "OP_NO_TLSv1_3", None) is None:
                raise ConfigError(
                    (
                        "federation_client_minimum_tls_version cannot be 1.3, "
                        "your OpenSSL does not support it"
                    )
                )

        # Whitelist of domains to not verify certificates for
        fed_whitelist_entries = config.get(
            "federation_certificate_verification_whitelist", []
        )

        # Support globs (*) in whitelist values
        self.federation_certificate_verification_whitelist = []
        for entry in fed_whitelist_entries:
            try:
                entry_regex = glob_to_regex(entry.encode("ascii").decode("ascii"))
            except UnicodeEncodeError:
                raise ConfigError(
                    "IDNA domain names are not allowed in the "
                    "federation_certificate_verification_whitelist: %s" % (entry,)
                )

            # Convert globs to regex
            self.federation_certificate_verification_whitelist.append(entry_regex)

        # List of custom certificate authorities for federation traffic validation
        custom_ca_list = config.get("federation_custom_ca_list", None)

        # Read in and parse custom CA certificates
        self.federation_ca_trust_root = None
        if custom_ca_list is not None:
            if len(custom_ca_list) == 0:
                # A trustroot cannot be generated without any CA certificates.
                # Raise an error if this option has been specified without any
                # corresponding certificates.
                raise ConfigError(
                    "federation_custom_ca_list specified without "
                    "any certificate files"
                )

            certs = []
            for ca_file in custom_ca_list:
                logger.debug("Reading custom CA certificate file: %s", ca_file)
                content = self.read_file(ca_file, "federation_custom_ca_list")

                # Parse the CA certificates
                try:
                    cert_base = Certificate.loadPEM(content)
                    certs.append(cert_base)
                except Exception as e:
                    raise ConfigError(
                        "Error parsing custom CA certificate file %s: %s" % (ca_file, e)
                    )

            self.federation_ca_trust_root = trustRootFromCertificates(certs)

        # This config option applies to non-federation HTTP clients
        # (e.g. for talking to recaptcha, identity servers, and such)
        # It should never be used in production, and is intended for
        # use only when running tests.
        self.use_insecure_ssl_client_just_for_testing_do_not_use = config.get(
            "use_insecure_ssl_client_just_for_testing_do_not_use"
        )

        self.tls_certificate = None
        self.tls_private_key = None