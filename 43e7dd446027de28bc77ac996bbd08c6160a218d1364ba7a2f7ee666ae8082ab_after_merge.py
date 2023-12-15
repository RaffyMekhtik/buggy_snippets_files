    def groupby(
        self,
        by=None,
        axis=0,
        level=None,
        as_index=True,
        sort=True,
        group_keys=True,
        squeeze=False,
        observed=False,
    ):
        """Apply a groupby to this DataFrame. See _groupby() remote task.
        Args:
            by: The value to groupby.
            axis: The axis to groupby.
            level: The level of the groupby.
            as_index: Whether or not to store result as index.
            sort: Whether or not to sort the result by the index.
            group_keys: Whether or not to group the keys.
            squeeze: Whether or not to squeeze.
        Returns:
            A new DataFrame resulting from the groupby.
        """
        axis = self._get_axis_number(axis)
        idx_name = None
        # Drop here indicates whether or not to drop the data column before doing the
        # groupby. The typical pandas behavior is to drop when the data came from this
        # dataframe. When a string, Series directly from this dataframe, or list of
        # strings is passed in, the data used for the groupby is dropped before the
        # groupby takes place.
        drop = False

        if (
            not isinstance(by, (pandas.Series, Series))
            and is_list_like(by)
            and len(by) == 1
        ):
            by = by[0]

        if callable(by):
            by = self.index.map(by)
        elif isinstance(by, str):
            drop = by in self.columns
            idx_name = by
            if (
                self._query_compiler.has_multiindex(axis=axis)
                and by in self.axes[axis].names
            ):
                # In this case we pass the string value of the name through to the
                # partitions. This is more efficient than broadcasting the values.
                pass
            else:
                by = self.__getitem__(by)._query_compiler
        elif isinstance(by, Series):
            drop = by._parent is self
            idx_name = by.name
            by = by._query_compiler
        elif is_list_like(by):
            # fastpath for multi column groupby
            if (
                not isinstance(by, Series)
                and axis == 0
                and all(
                    (
                        (isinstance(o, str) and (o in self))
                        or (isinstance(o, Series) and (o._parent is self))
                    )
                    for o in by
                )
            ):
                # We can just revert Series back to names because the parent is
                # this dataframe:
                by = [o.name if isinstance(o, Series) else o for o in by]
                by = self.__getitem__(by)._query_compiler
                drop = True
            else:
                mismatch = len(by) != len(self.axes[axis])
                if mismatch and all(
                    isinstance(obj, str)
                    and (
                        obj in self
                        or (hasattr(self.index, "names") and obj in self.index.names)
                    )
                    for obj in by
                ):
                    # In the future, we will need to add logic to handle this, but for now
                    # we default to pandas in this case.
                    pass
                elif mismatch and any(
                    isinstance(obj, str) and obj not in self.columns for obj in by
                ):
                    names = [o.name if isinstance(o, Series) else o for o in by]
                    raise KeyError(next(x for x in names if x not in self))
        return DataFrameGroupBy(
            self,
            by,
            axis,
            level,
            as_index,
            sort,
            group_keys,
            squeeze,
            idx_name,
            observed=observed,
            drop=drop,
        )