  def __init__(self, timestamp, offset, attributes):
    """Initializes a text event.

    Args:
      timestamp (int): timestamp, which contains the number of microseconds
          since January 1, 1970, 00:00:00 UTC.
      offset (int): offset of the text event within the event source.
      attributes (dict[str,object]): event attributes.
    """
    super(TextEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.WRITTEN_TIME)

    self.offset = offset

    for name, value in iter(attributes.items()):
      # TODO: Revisit this constraints and see if we can implement
      # it using a more sane solution.
      if isinstance(value, py2to3.STRING_TYPES) and not value:
        continue
      setattr(self, name, value)