    def __init__(
        self,
        typ,
        filename,
        lineno,
        secret,
        is_secret=None,
    ):
        """
        :type typ: str
        :param typ: human-readable secret type, defined by the plugin
                    that generated this PotentialSecret.
                    e.g. "High Entropy String"

        :type filename: str
        :param filename: name of file that this secret was found

        :type lineno: int
        :param lineno: location of secret, within filename.
                       Merely used as a reference for easy triage.

        :type secret: str
        :param secret: the actual secret identified

        :type is_secret: bool|None
        :param is_secret: whether or not the secret is a true- or false- positive
        """
        self.type = typ
        self.filename = filename
        self.lineno = lineno
        self.secret_hash = self.hash_secret(secret)
        self.is_secret = is_secret

        # If two PotentialSecrets have the same values for these fields,
        # they are considered equal. Note that line numbers aren't included
        # in this, because line numbers are subject to change.
        self.fields_to_compare = ['filename', 'secret_hash', 'type']