    def __call__(self, target: DataFrame, value):
        raw_target = target

        inputs = [target]
        if np.isscalar(value):
            value_dtype = np.array(value).dtype
        elif self._is_scalar_tensor(value):
            inputs.append(value)
            value_dtype = value.dtype
        else:
            if isinstance(value, (pd.Series, SERIES_TYPE)):
                value = asseries(value)
                value_dtype = value.dtype
            elif is_list_like(value) or isinstance(value, TENSOR_TYPE):
                value = asseries(value, index=target.index)
                value_dtype = value.dtype
            else:  # pragma: no cover
                raise TypeError('Wrong value type, could be one of scalar, Series or tensor')

            if target.shape[0] == 0:
                # target empty, reindex target first
                target = target.reindex(value.index)
                inputs[0] = target
            elif value.index_value.key != target.index_value.key:
                # need reindex when target df is not empty and index different
                value = value.reindex(target.index)
            inputs.append(value)

        index_value = target.index_value
        dtypes = target.dtypes.copy(deep=True)
        dtypes.loc[self._indexes] = value_dtype
        columns_value = parse_index(dtypes.index, store_data=True)
        ret = self.new_dataframe(inputs, shape=(target.shape[0], len(dtypes)),
                                 dtypes=dtypes, index_value=index_value,
                                 columns_value=columns_value)
        raw_target.data = ret.data