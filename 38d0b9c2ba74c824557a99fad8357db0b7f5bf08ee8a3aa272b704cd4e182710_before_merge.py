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
        drop = False
        if callable(by):
            by = self.index.map(by)
        elif isinstance(by, str):
            drop = by in self.columns
            idx_name = by
            if (
                isinstance(self.axes[axis], pandas.MultiIndex)
                and by in self.axes[axis].names
            ):
                # In this case we pass the string value of the name through to the
                # partitions. This is more efficient than broadcasting the values.
                pass
            else:
                by = self.__getitem__(by)._query_compiler
        elif isinstance(by, Series):
            idx_name = by.name
            by = by._query_compiler
        elif is_list_like(by):
            # fastpath for multi column groupby
            if not isinstance(by, Series) and axis == 0 and all(o in self for o in by):
                warnings.warn(
                    "Multi-column groupby is a new feature. "
                    "Please report any bugs/issues to bug_reports@modin.org."
                )
                by = self.__getitem__(by)._query_compiler
            else:
                mismatch = len(by) != len(self.axes[axis])
                if mismatch and all(
                    obj in self
                    or (hasattr(self.index, "names") and obj in self.index.names)
                    for obj in by
                ):
                    # In the future, we will need to add logic to handle this, but for now
                    # we default to pandas in this case.
                    pass
                elif mismatch:
                    raise KeyError(next(x for x in by if x not in self))

        from .groupby import DataFrameGroupBy

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