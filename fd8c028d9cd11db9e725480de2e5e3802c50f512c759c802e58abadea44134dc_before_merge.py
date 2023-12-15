    async def async_send_mobilepush(self, message, **kwargs):
        """Send push to the media player's associated mobile devices."""
        await self.alexa_api.send_mobilepush(
            message, customer_id=self._customer_id, **kwargs
        )