def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the HomeMatic sensor platform."""
    if discovery_info is None:
        return

    devices = []
    for conf in discovery_info[ATTR_DISCOVER_DEVICES]:
        new_device = HMSensor(conf)
        devices.append(new_device)

    add_entities(devices)