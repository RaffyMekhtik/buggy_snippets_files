    async def _connect_tcp(self, target_addr):
        try:
            socket.inet_aton(target_addr[0])
            address_type = ADDRESS_TYPE_IPV4
        except (ValueError, OSError):
            address_type = ADDRESS_TYPE_DOMAIN_NAME

        request = CommandRequest(SOCKS_VERSION, REQ_CMD_CONNECT, 0, (address_type, *target_addr))
        data = await self._send(socks5_serializer.pack_serializable(request))
        response, _ = socks5_serializer.unpack_serializable(CommandResponse, data)

        if response.version != SOCKS_VERSION:
            raise Socks5Error('Unsupported proxy server')

        if response.reply > 0:
            raise Socks5Error('TCP connect failed')

        self.connected_to = target_addr