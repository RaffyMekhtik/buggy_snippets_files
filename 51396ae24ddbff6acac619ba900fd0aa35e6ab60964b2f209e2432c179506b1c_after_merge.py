    def check(self, instance):
        service_check_msg = None
        offset_threshold = instance.get('offset_threshold', DEFAULT_OFFSET_THRESHOLD)
        custom_tags = instance.get('tags', [])
        try:
            offset_threshold = int(offset_threshold)
        except (TypeError, ValueError):
            msg = "Must specify an integer value for offset_threshold. Configured value is {}".format(offset_threshold)
            raise Exception(msg)

        req_args = {
            'host': instance.get('host', DEFAULT_HOST),
            'port': self._get_service_port(instance),
            'version': int(instance.get('version', DEFAULT_VERSION)),
            'timeout': float(instance.get('timeout', DEFAULT_TIMEOUT)),
        }

        self.log.debug("Using ntp host: {}".format(req_args['host']))

        try:
            ntp_stats = ntplib.NTPClient().request(**req_args)
        except ntplib.NTPException:
            self.log.debug("Could not connect to NTP Server {}".format(
                req_args['host']))
            status = AgentCheck.UNKNOWN
            ntp_ts = None
        else:
            ntp_offset = ntp_stats.offset

            # Use the ntp server's timestamp for the time of the result in
            # case the agent host's clock is messed up.
            ntp_ts = ntp_stats.recv_time
            self.gauge('ntp.offset', ntp_offset, timestamp=ntp_ts, tags=custom_tags)

            if abs(ntp_offset) > offset_threshold:
                status = AgentCheck.CRITICAL
                service_check_msg = "Offset {} secs higher than offset threshold ({} secs)".format(ntp_offset,
                                                                                                   offset_threshold)
            else:
                status = AgentCheck.OK

        self.service_check('ntp.in_sync', status, timestamp=ntp_ts, message=service_check_msg, tags=custom_tags)