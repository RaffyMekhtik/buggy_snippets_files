    def from_path(
        cls,
        archive_path: str,
        predictor_name: str = None,
        cuda_device: int = -1,
        dataset_reader_to_load: str = "validation",
        frozen: bool = True,
        import_plugins: bool = True,
    ) -> "Predictor":
        """
        Instantiate a `Predictor` from an archive path.

        If you need more detailed configuration options, such as overrides,
        please use `from_archive`.

        # Parameters

        archive_path : `str`
            The path to the archive.
        predictor_name : `str`, optional (default=`None`)
            Name that the predictor is registered as, or None to use the
            predictor associated with the model.
        cuda_device : `int`, optional (default=`-1`)
            If `cuda_device` is >= 0, the model will be loaded onto the
            corresponding GPU. Otherwise it will be loaded onto the CPU.
        dataset_reader_to_load : `str`, optional (default=`"validation"`)
            Which dataset reader to load from the archive, either "train" or
            "validation".
        frozen : `bool`, optional (default=`True`)
            If we should call `model.eval()` when building the predictor.
        import_plugins : `bool`, optional (default=`True`)
            If `True`, we attempt to import plugins before loading the predictor.
            This comes with additional overhead, but means you don't need to explicitly
            import the modules that your predictor depends on as long as those modules
            can be found by `allennlp.common.plugins.import_plugins()`.

        # Returns

        `Predictor`
            A Predictor instance.
        """
        if import_plugins:
            plugins.import_plugins()
        return Predictor.from_archive(
            load_archive(archive_path, cuda_device=cuda_device),
            predictor_name,
            dataset_reader_to_load=dataset_reader_to_load,
            frozen=frozen,
        )