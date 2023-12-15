    async def start_notify(
        self, _uuid: str, callback: Callable[[str, Any], Any], **kwargs
    ) -> None:
        """Starts a notification session from a characteristic.

        Args:
            _uuid (str or uuid.UUID): The UUID of the GATT
            characteristic to start subscribing to notifications from.
            callback (Callable): A function that will be called on notification.

        Keyword Args:
            notification_wrapper (bool): Set to `False` to avoid parsing of
            notification to bytearray.

        """
        _wrap = kwargs.get("notification_wrapper", True)
        char_props = self.characteristics.get(_uuid)
        await self._bus.callRemote(
            char_props.get("Path"),
            "StartNotify",
            interface=defs.GATT_CHARACTERISTIC_INTERFACE,
            destination=defs.BLUEZ_SERVICE,
            signature="",
            body=[],
            returnSignature="",
        ).asFuture(self.loop)

        if _wrap:
            self._notification_callbacks[
                char_props.get("Path")
            ] = _data_notification_wrapper(
                callback, self._char_path_to_uuid
            )  # noqa | E123 error in flake8...
        else:
            self._notification_callbacks[
                char_props.get("Path")
            ] = _regular_notification_wrapper(
                callback, self._char_path_to_uuid
            )  # noqa | E123 error in flake8...