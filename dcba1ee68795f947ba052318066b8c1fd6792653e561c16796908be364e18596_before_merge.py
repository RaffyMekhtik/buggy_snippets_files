    def read_config(self, config):
        consent_config = config.get("user_consent")
        if consent_config is None:
            return
        self.user_consent_version = str(consent_config["version"])
        self.user_consent_template_dir = consent_config["template_dir"]
        self.user_consent_server_notice_content = consent_config.get(
            "server_notice_content",
        )
        self.block_events_without_consent_error = consent_config.get(
            "block_events_error",
        )
        self.user_consent_server_notice_to_guests = bool(consent_config.get(
            "send_server_notice_to_guests", False,
        ))
        self.user_consent_at_registration = bool(consent_config.get(
            "require_at_registration", False,
        ))
        self.user_consent_policy_name = consent_config.get(
            "policy_name", "Privacy Policy",
        )