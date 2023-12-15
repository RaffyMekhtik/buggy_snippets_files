    def fetch_external(self, paths: Iterable, **kwargs):
        """Fetch specified external repo paths into cache.

        Returns 3-tuple in the form
            (downloaded, failed, list(cache_infos))
        where cache_infos can be used as checkout targets for the
        fetched paths.
        """
        download_results = []
        failed = 0

        paths = [PathInfo(self.root_dir) / path for path in paths]

        def download_update(result):
            download_results.append(result)

        hash_infos = []
        for path in paths:
            if not self.repo_tree.exists(path):
                raise PathMissingError(path, self.url)
            hash_info = self.repo_tree.get_hash(
                path, download_callback=download_update
            ).to_dict()
            self.local_cache.save(
                path,
                self.repo_tree,
                hash_info,
                save_link=False,
                download_callback=download_update,
            )
            hash_infos.append(hash_info)

        return sum(download_results), failed, hash_infos