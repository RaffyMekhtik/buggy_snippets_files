    def _get_granular_checksum(
        self, path_info: PathInfo, out: "BaseOutput", remote=None
    ):
        assert isinstance(path_info, PathInfo)
        if not self.fetch and not self.stream:
            raise FileNotFoundError
        dir_cache = out.get_dir_cache(remote=remote)
        for entry in dir_cache:
            entry_relpath = entry[out.tree.PARAM_RELPATH]
            if os.name == "nt":
                entry_relpath = entry_relpath.replace("/", os.sep)
            if path_info == out.path_info / entry_relpath:
                return entry[out.tree.PARAM_CHECKSUM]
        raise FileNotFoundError