    async def async_added_to_hass(self):
        """Store register state change callback."""
        try:
            if not self.enabled:
                return
        except AttributeError:
            pass
        # Register event handler on bus
        self._listener = self.hass.bus.async_listen(
            f"{ALEXA_DOMAIN}_{hide_email(self._account)}"[0:32], self._handle_event
        )
        await self.async_update()