    def execute(cls, ctx, op):
        def _base_concat(chunk, inputs):
            # auto generated concat when executing a DataFrame, Series or Index
            if chunk.op.object_type == ObjectType.dataframe:
                return _auto_concat_dataframe_chunks(chunk, inputs)
            elif chunk.op.object_type == ObjectType.series:
                return _auto_concat_series_chunks(chunk, inputs)
            else:
                raise TypeError('Only DataFrameChunk, SeriesChunk and IndexChunk '
                                'can be automatically concatenated')

        def _auto_concat_dataframe_chunks(chunk, inputs):
            if chunk.op.axis is not None:
                return pd.concat(inputs, axis=op.axis)
            # auto generated concat when executing a DataFrame
            n_rows = max(inp.index[0] for inp in chunk.inputs) + 1
            n_cols = int(len(inputs) // n_rows)
            assert n_rows * n_cols == len(inputs)

            xdf = pd if isinstance(inputs[0], pd.DataFrame) else cudf

            concats = []
            for i in range(n_rows):
                concat = xdf.concat([inputs[i * n_cols + j] for j in range(n_cols)], axis=1)
                concats.append(concat)

            if xdf is pd:
                # The `sort=False` is to suppress a `FutureWarning` of pandas, when the index or column of chunks to
                # concatenate is not aligned, which may happens for certain ops.
                #
                # See also Note [Columns of Left Join] in test_merge_execution.py.
                ret = xdf.concat(concats, sort=False)
            else:
                ret = xdf.concat(concats)
                # cuDF will lost index name when concat two seriess.
                ret.index.name = concats[0].index.name
            if getattr(chunk.index_value, 'should_be_monotonic', False):
                ret.sort_index(inplace=True)
            if getattr(chunk.columns_value, 'should_be_monotonic', False):
                ret.sort_index(axis=1, inplace=True)
            return ret

        def _auto_concat_series_chunks(chunk, inputs):
            # auto generated concat when executing a Series
            if all(np.isscalar(inp) for inp in inputs):
                return pd.Series(inputs)
            else:
                xdf = pd if isinstance(inputs[0], pd.Series) else cudf
                if chunk.op.axis is not None:
                    concat = xdf.concat(inputs, axis=chunk.op.axis)
                else:
                    concat = xdf.concat(inputs)
                if getattr(chunk.index_value, 'should_be_monotonic', False):
                    concat.sort_index(inplace=True)
                return concat

        chunk = op.outputs[0]
        inputs = [ctx[input.key] for input in op.inputs]

        if isinstance(inputs[0], tuple):
            ctx[chunk.key] = tuple(_base_concat(chunk, [input[i] for input in inputs])
                                   for i in range(len(inputs[0])))
        else:
            ctx[chunk.key] = _base_concat(chunk, inputs)