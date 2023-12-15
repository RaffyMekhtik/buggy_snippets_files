    def __repr__(self):
        if self.tls_established and self.sni:
            tls = "[{}: {}] ".format(self.tls_version or "TLS", self.sni)
        elif self.tls_established:
            tls = "[{}] ".format(self.tls_version or "TLS")
        else:
            tls = ""
        if self.alpn_proto_negotiated:
            alpn = "[ALPN: {}] ".format(
                strutils.bytes_to_escaped_str(self.alpn_proto_negotiated)
            )
        else:
            alpn = ""
        return "<ServerConnection: {tls}{alpn}{address}>".format(
            tls=tls,
            alpn=alpn,
            address=human.format_address(self.address),
        )