    def _read(cls, filepath_or_buffer, **kwargs):
        filepath_or_buffer = cls.get_path_or_buffer(filepath_or_buffer)
        if isinstance(filepath_or_buffer, str):
            if not cls.file_exists(filepath_or_buffer):
                return cls.single_worker_read(filepath_or_buffer, **kwargs)
            filepath_or_buffer = cls.get_path(filepath_or_buffer)
        elif not cls.pathlib_or_pypath(filepath_or_buffer):
            return cls.single_worker_read(filepath_or_buffer, **kwargs)
        compression_type = cls.infer_compression(
            filepath_or_buffer, kwargs.get("compression")
        )
        if compression_type is not None:
            if (
                compression_type == "gzip"
                or compression_type == "bz2"
                or compression_type == "xz"
            ):
                kwargs["compression"] = compression_type
            elif (
                compression_type == "zip"
                and sys.version_info[0] == 3
                and sys.version_info[1] >= 7
            ):
                # need python3.7 to .seek and .tell ZipExtFile
                kwargs["compression"] = compression_type
            else:
                return cls.single_worker_read(filepath_or_buffer, **kwargs)

        chunksize = kwargs.get("chunksize")
        if chunksize is not None:
            return cls.single_worker_read(filepath_or_buffer, **kwargs)

        skiprows = kwargs.get("skiprows")
        if skiprows is not None and not isinstance(skiprows, int):
            return cls.single_worker_read(filepath_or_buffer, **kwargs)
        nrows = kwargs.pop("nrows", None)
        names = kwargs.get("names", None)
        index_col = kwargs.get("index_col", None)
        usecols = kwargs.get("usecols", None)
        encoding = kwargs.get("encoding", None)
        if names is None:
            # For the sake of the empty df, we assume no `index_col` to get the correct
            # column names before we build the index. Because we pass `names` in, this
            # step has to happen without removing the `index_col` otherwise it will not
            # be assigned correctly
            names = pandas.read_csv(
                filepath_or_buffer,
                **dict(kwargs, usecols=None, nrows=0, skipfooter=0, index_col=None),
            ).columns
        elif index_col is None and not usecols:
            # When names is set to some list that is smaller than the number of columns
            # in the file, the first columns are built as a hierarchical index.
            empty_pd_df = pandas.read_csv(
                filepath_or_buffer, nrows=0, encoding=encoding
            )
            num_cols = len(empty_pd_df.columns)
            if num_cols > len(names):
                index_col = list(range(num_cols - len(names)))
                if len(index_col) == 1:
                    index_col = index_col[0]
                kwargs["index_col"] = index_col
        empty_pd_df = pandas.read_csv(
            filepath_or_buffer, **dict(kwargs, nrows=0, skipfooter=0)
        )
        column_names = empty_pd_df.columns
        skipfooter = kwargs.get("skipfooter", None)
        skiprows = kwargs.pop("skiprows", None)
        parse_dates = kwargs.pop("parse_dates", False)
        partition_kwargs = dict(
            kwargs,
            header=None,
            names=names,
            skipfooter=0,
            skiprows=None,
            parse_dates=parse_dates,
        )
        encoding = kwargs.get("encoding", None)
        quotechar = kwargs.get("quotechar", '"').encode(
            encoding if encoding is not None else "UTF-8"
        )
        is_quoting = kwargs.get("quoting", "") != csv.QUOTE_NONE
        with cls.file_open(filepath_or_buffer, "rb", compression_type) as f:
            # Skip the header since we already have the header information and skip the
            # rows we are told to skip.
            if isinstance(skiprows, int) or skiprows is None:
                if skiprows is None:
                    skiprows = 0
                header = kwargs.get("header", "infer")
                if header == "infer" and kwargs.get("names", None) is None:
                    skiprows += 1
                elif isinstance(header, int):
                    skiprows += header + 1
                elif hasattr(header, "__iter__") and not isinstance(header, str):
                    skiprows += max(header) + 1
            if kwargs.get("encoding", None) is not None:
                partition_kwargs["skiprows"] = 1
            # Launch tasks to read partitions
            partition_ids = []
            index_ids = []
            dtypes_ids = []
            # Max number of partitions available
            num_partitions = NPartitions.get()
            # This is the number of splits for the columns
            num_splits = min(len(column_names), num_partitions)
            # Metadata
            column_chunksize = compute_chunksize(empty_pd_df, num_splits, axis=1)
            if column_chunksize > len(column_names):
                column_widths = [len(column_names)]
                # This prevents us from unnecessarily serializing a bunch of empty
                # objects.
                num_splits = 1
            else:
                column_widths = [
                    column_chunksize
                    if len(column_names) > (column_chunksize * (i + 1))
                    else 0
                    if len(column_names) < (column_chunksize * i)
                    else len(column_names) - (column_chunksize * i)
                    for i in range(num_splits)
                ]

            args = {
                "fname": filepath_or_buffer,
                "num_splits": num_splits,
                **partition_kwargs,
            }

            splits = cls.partitioned_file(
                f,
                num_partitions=num_partitions,
                nrows=nrows,
                skiprows=skiprows,
                quotechar=quotechar,
                is_quoting=is_quoting,
            )
            for start, end in splits:
                args.update({"start": start, "end": end})
                partition_id = cls.deploy(cls.parse, num_splits + 2, args)
                partition_ids.append(partition_id[:-2])
                index_ids.append(partition_id[-2])
                dtypes_ids.append(partition_id[-1])

        # Compute the index based on a sum of the lengths of each partition (by default)
        # or based on the column(s) that were requested.
        if index_col is None:
            row_lengths = cls.materialize(index_ids)
            new_index = pandas.RangeIndex(sum(row_lengths))
        else:
            index_objs = cls.materialize(index_ids)
            row_lengths = [len(o) for o in index_objs]
            new_index = index_objs[0].append(index_objs[1:])
            new_index.name = empty_pd_df.index.name

        # Compute dtypes by getting collecting and combining all of the partitions. The
        # reported dtypes from differing rows can be different based on the inference in
        # the limited data seen by each worker. We use pandas to compute the exact dtype
        # over the whole column for each column. The index is set below.
        dtypes = cls.get_dtypes(dtypes_ids) if len(dtypes_ids) > 0 else None

        partition_ids = cls.build_partition(partition_ids, row_lengths, column_widths)
        # If parse_dates is present, the column names that we have might not be
        # the same length as the returned column names. If we do need to modify
        # the column names, we remove the old names from the column names and
        # insert the new one at the front of the Index.
        if parse_dates is not None:
            # We have to recompute the column widths if `parse_dates` is set because
            # we are not guaranteed to have the correct information regarding how many
            # columns are on each partition.
            column_widths = None
            # Check if is list of lists
            if isinstance(parse_dates, list) and isinstance(parse_dates[0], list):
                for group in parse_dates:
                    new_col_name = "_".join(group)
                    column_names = column_names.drop(group).insert(0, new_col_name)
            # Check if it is a dictionary
            elif isinstance(parse_dates, dict):
                for new_col_name, group in parse_dates.items():
                    column_names = column_names.drop(group).insert(0, new_col_name)
        # Set the index for the dtypes to the column names
        if isinstance(dtypes, pandas.Series):
            dtypes.index = column_names
        else:
            dtypes = pandas.Series(dtypes, index=column_names)
        new_frame = cls.frame_cls(
            partition_ids,
            new_index,
            column_names,
            row_lengths,
            column_widths,
            dtypes=dtypes,
        )
        new_query_compiler = cls.query_compiler_cls(new_frame)

        if skipfooter:
            new_query_compiler = new_query_compiler.drop(
                new_query_compiler.index[-skipfooter:]
            )
        if kwargs.get("squeeze", False) and len(new_query_compiler.columns) == 1:
            return new_query_compiler[new_query_compiler.columns[0]]
        if index_col is None:
            new_query_compiler._modin_frame._apply_index_objs(axis=0)
        return new_query_compiler