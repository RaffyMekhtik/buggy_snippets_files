    def rename(self, *args, **kwargs):
        """
        Alter axes input function or functions. Function / dict values must be
        unique (1-to-1). Labels not contained in a dict / Series will be left
        as-is. Extra labels listed don't throw an error. Alternatively, change
        ``Series.name`` with a scalar value (Series only).

        Parameters
        ----------
        %(axes)s : scalar, list-like, dict-like or function, optional
            Scalar or list-like will alter the ``Series.name`` attribute,
            and raise on DataFrame.
            dict-like or functions are transformations to apply to
            that axis' values
        copy : bool, default True
            Also copy underlying data.
        inplace : bool, default False
            Whether to return a new %(klass)s. If True then value of copy is
            ignored.
        level : int or level name, default None
            In case of a MultiIndex, only rename labels in the specified
            level.
        errors : {'ignore', 'raise'}, default 'ignore'
            If 'raise', raise a `KeyError` when a dict-like `mapper`, `index`,
            or `columns` contains labels that are not present in the Index
            being transformed.
            If 'ignore', existing keys will be renamed and extra keys will be
            ignored.

        Returns
        -------
        renamed : %(klass)s (new object)

        Raises
        ------
        KeyError
            If any of the labels is not found in the selected axis and
            "errors='raise'".

        See Also
        --------
        NDFrame.rename_axis

        Examples
        --------

        >>> s = pd.Series([1, 2, 3])
        >>> s
        0    1
        1    2
        2    3
        dtype: int64
        >>> s.rename("my_name") # scalar, changes Series.name
        0    1
        1    2
        2    3
        Name: my_name, dtype: int64
        >>> s.rename(lambda x: x ** 2)  # function, changes labels
        0    1
        1    2
        4    3
        dtype: int64
        >>> s.rename({1: 3, 2: 5})  # mapping, changes labels
        0    1
        3    2
        5    3
        dtype: int64

        Since ``DataFrame`` doesn't have a ``.name`` attribute,
        only mapping-type arguments are allowed.

        >>> df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        >>> df.rename(2)
        Traceback (most recent call last):
        ...
        TypeError: 'int' object is not callable

        ``DataFrame.rename`` supports two calling conventions

        * ``(index=index_mapper, columns=columns_mapper, ...)``
        * ``(mapper, axis={'index', 'columns'}, ...)``

        We *highly* recommend using keyword arguments to clarify your
        intent.

        >>> df.rename(index=str, columns={"A": "a", "B": "c"})
           a  c
        0  1  4
        1  2  5
        2  3  6

        >>> df.rename(index=str, columns={"A": "a", "C": "c"})
           a  B
        0  1  4
        1  2  5
        2  3  6

        Using axis-style parameters

        >>> df.rename(str.lower, axis='columns')
           a  b
        0  1  4
        1  2  5
        2  3  6

        >>> df.rename({1: 2, 2: 4}, axis='index')
           A  B
        0  1  4
        2  2  5
        4  3  6

        See the :ref:`user guide <basics.rename>` for more.
        """
        axes, kwargs = self._construct_axes_from_arguments(args, kwargs)
        copy = kwargs.pop("copy", True)
        inplace = kwargs.pop("inplace", False)
        level = kwargs.pop("level", None)
        axis = kwargs.pop("axis", None)
        errors = kwargs.pop("errors", "ignore")
        if axis is not None:
            # Validate the axis
            self._get_axis_number(axis)

        if kwargs:
            raise TypeError(
                "rename() got an unexpected keyword "
                f'argument "{list(kwargs.keys())[0]}"'
            )

        if com.count_not_none(*axes.values()) == 0:
            raise TypeError("must pass an index to rename")

        self._consolidate_inplace()
        result = self if inplace else self.copy(deep=copy)

        # start in the axis order to eliminate too many copies
        for axis in range(self._AXIS_LEN):
            v = axes.get(self._AXIS_NAMES[axis])
            if v is None:
                continue
            f = com.get_rename_function(v)
            baxis = self._get_block_manager_axis(axis)
            if level is not None:
                level = self.axes[axis]._get_level_number(level)

            # GH 13473
            if not callable(v):
                indexer = self.axes[axis].get_indexer_for(v)
                if errors == "raise" and len(indexer[indexer == -1]):
                    missing_labels = [
                        label for index, label in enumerate(v) if indexer[index] == -1
                    ]
                    raise KeyError(f"{missing_labels} not found in axis")

            result._data = result._data.rename_axis(
                f, axis=baxis, copy=copy, level=level
            )
            result._clear_item_cache()

        if inplace:
            self._update_inplace(result._data)
        else:
            return result.__finalize__(self)