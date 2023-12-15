    def check_channels_updates(self):
        """
        Check whether there are channels that are updated. If so, download the new version of the channel.
        """
        # FIXME: These naughty try-except-pass workarounds are necessary to keep the loop going in all circumstances

        with db_session:
            channels_queue = list(self.session.lm.mds.ChannelMetadata.get_updated_channels())

        for channel in channels_queue:
            try:
                if not self.session.has_download(str(channel.infohash)):
                    self._logger.info("Downloading new channel version %s ver %i->%i",
                                      hexlify(str(channel.public_key)),
                                      channel.local_version, channel.timestamp)
                    self.download_channel(channel)
            except Exception:
                self._logger.exception("Error when tried to download a newer version of channel %s",
                                       hexlify(channel.public_key))