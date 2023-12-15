    async def start_notify(
        self, _uuid: str, callback: Callable[[str, Any], Any], **kwargs
    ) -> None:
        """Activate notifications on a characteristic.

        Callbacks must accept two inputs. The first will be a uuid string
        object and the second will be a bytearray.

        .. code-block:: python

            def callback(sender, data):
                print(f"{sender}: {data}")
            client.start_notify(char_uuid, callback)

        Args:
            _uuid (str or UUID): The uuid of the characteristics to start notification on.
            callback (function): The function to be called on notification.

        """
        characteristic = self.characteristics.get(str(_uuid))

        if self._notification_callbacks.get(str(_uuid)):
            await self.stop_notify(_uuid)

        dotnet_callback = TypedEventHandler[GattCharacteristic, Array[Byte]](
            _notification_wrapper(callback)
        )
        status = await wrap_Task(
            self._bridge.StartNotify(characteristic, dotnet_callback), loop=self.loop
        )
        if status != GattCommunicationStatus.Success:
            raise BleakError(
                "Could not start notify on {0}: {1}",
                characteristic.Uuid.ToString(),
                status,
            )