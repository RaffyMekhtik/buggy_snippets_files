    def _read(cls, path, engine, columns, **kwargs):
        """Load a parquet object from the file path, returning a Modin DataFrame.

        Modin only supports pyarrow engine for now.

        Parameters
        ----------
        path: str
            The filepath of the parquet file in local filesystem or hdfs.
        engine: 'pyarrow'
            Parquet library to use
        columns: list or None
            If not None, only these columns will be read from the file.
        kwargs: dict
            Keyword arguments.

        Returns
        -------
        PandasQueryCompiler
            A new Query Compiler.

        Notes
        -----
        ParquetFile API is used. Please refer to the documentation here
        https://arrow.apache.org/docs/python/parquet.html
        """
        from pyarrow.parquet import ParquetFile, ParquetDataset
        from modin.pandas.io import PQ_INDEX_REGEX

        if isinstance(path, str) and os.path.isdir(path):
            partitioned_columns = set()
            directory = True
            # We do a tree walk of the path directory because partitioned
            # parquet directories have a unique column at each directory level.
            # Thus, we can use os.walk(), which does a dfs search, to walk
            # through the different columns that the data is partitioned on
            for (root, dir_names, files) in os.walk(path):
                if dir_names:
                    partitioned_columns.add(dir_names[0].split("=")[0])
                if files:
                    # Metadata files, git files, .DSStore
                    if files[0][0] == ".":
                        continue
                    break
            partitioned_columns = list(partitioned_columns)
            if len(partitioned_columns):
                ErrorMessage.default_to_pandas("Mixed Partitioning Columns in Parquet")
                return cls.single_worker_read(
                    path, engine=engine, columns=columns, **kwargs
                )
        else:
            directory = False
        if not columns:
            import s3fs

            if directory:
                # Path of the sample file that we will read to get the remaining columns
                pd = ParquetDataset(path)
                meta = pd.metadata
                column_names = pd.schema.names
            elif isinstance(path, str) and path.startswith("hdfs://"):
                import fsspec.core

                fs, path = fsspec.core.url_to_fs(path)
                pd = ParquetDataset(path, filesystem=fs)
                meta = pd.metadata
                column_names = pd.schema.names
            elif isinstance(path, s3fs.S3File) or (
                isinstance(path, str) and path.startswith("s3://")
            ):
                from botocore.exceptions import NoCredentialsError

                if isinstance(path, s3fs.S3File):
                    bucket_path = path.url().split(".s3.amazonaws.com")
                    path = "s3://" + bucket_path[0].split("://")[1] + bucket_path[1]
                try:
                    fs = s3fs.S3FileSystem()
                    pd = ParquetDataset(path, filesystem=fs)
                except NoCredentialsError:
                    fs = s3fs.S3FileSystem(anon=True)
                    pd = ParquetDataset(path, filesystem=fs)
                meta = pd.metadata
                column_names = pd.schema.names
            else:
                meta = ParquetFile(path).metadata
                column_names = meta.schema.names
            if meta is not None:
                # This is how we convert the metadata from pyarrow to a python
                # dictionary, from which we then get the index columns.
                # We use these to filter out from the columns in the metadata since
                # the pyarrow storage has no concept of row labels/index.
                # This ensures that our metadata lines up with the partitions without
                # extra communication steps once we `have done all the remote
                # computation.
                index_columns = eval(
                    meta.metadata[b"pandas"].replace(b"null", b"None")
                ).get("index_columns", [])
                column_names = [c for c in column_names if c not in index_columns]
            columns = [name for name in column_names if not PQ_INDEX_REGEX.match(name)]
        return cls.build_query_compiler(path, columns, **kwargs)