    def _upload_package(self, pref, retry=None, retry_wait=None, integrity_check=False,
                        policy=None, p_remote=None):

        assert (pref.revision is not None), "Cannot upload a package without PREV"
        assert (pref.ref.revision is not None), "Cannot upload a package without RREV"

        conanfile_path = self._cache.package_layout(pref.ref).conanfile()
        self._hook_manager.execute("pre_upload_package", conanfile_path=conanfile_path,
                                   reference=pref.ref,
                                   package_id=pref.id,
                                   remote=p_remote)

        t1 = time.time()
        the_files = self._compress_package_files(pref, integrity_check)

        with self._cache.package_layout(pref.ref).update_metadata() as metadata:
            metadata.packages[pref.id].checksums = calc_files_checksum(the_files)

        if policy == UPLOAD_POLICY_SKIP:
            return None
        files_to_upload, deleted = self._package_files_to_upload(pref, policy, the_files, p_remote)

        if files_to_upload or deleted:
            self._remote_manager.upload_package(pref, files_to_upload, deleted, p_remote, retry,
                                                retry_wait)
            logger.debug("UPLOAD: Time upload package: %f" % (time.time() - t1))
        else:
            self._output.info("Package is up to date, upload skipped")

        duration = time.time() - t1
        log_package_upload(pref, duration, the_files, p_remote)
        self._hook_manager.execute("post_upload_package", conanfile_path=conanfile_path,
                                   reference=pref.ref, package_id=pref.id, remote=p_remote)

        logger.debug("UPLOAD: Time uploader upload_package: %f" % (time.time() - t1))

        metadata = self._cache.package_layout(pref.ref).load_metadata()
        cur_package_remote = metadata.packages[pref.id].remote
        if not cur_package_remote and policy != UPLOAD_POLICY_SKIP:
            with self._cache.package_layout(pref.ref).update_metadata() as metadata:
                metadata.packages[pref.id].remote = p_remote.name

        return pref