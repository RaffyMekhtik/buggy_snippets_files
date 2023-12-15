    def _init_data_struct(self):
        """Generate the data dictionary (self._data) from metadata."""
        self._state = "STATE"
        self._data.update({self._state: STATE_UNKNOWN})

        # Need sensor values for SwitchPowermeter
        for node in self._hmdevice.SENSORNODE:
            self._data.update({node: STATE_UNKNOWN})