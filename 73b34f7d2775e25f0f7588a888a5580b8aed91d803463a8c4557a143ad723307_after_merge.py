    def __contains__(self, name):
        """Simulate dict.__contains__() to handle DICOM keywords.

        This is called for code like:
        >>> ds = Dataset()
        >>> ds.SliceLocation = '2'
        >>> 'SliceLocation' in ds
        True

        Parameters
        ----------
        name : str or int or 2-tuple
            The Element keyword or tag to search for.

        Returns
        -------
        bool
            True if the DataElement is in the Dataset, False otherwise.
        """
        try:
            tag = Tag(name)
        except (ValueError, OverflowError):
            return False
        # Test against None as (0000,0000) is a possible tag
        if tag is not None:
            return tag in self._dict
        return name in self._dict  # will no doubt raise an exception