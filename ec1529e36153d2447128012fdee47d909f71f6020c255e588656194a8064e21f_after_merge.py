    def artifact(self, path, streamed=False, action=None, chunk_size=1024,
                 **kwargs):
        """Get a single artifact file from within the job's artifacts archive.

        Args:
            path (str): Path of the artifact
            streamed (bool): If True the data will be processed by chunks of
                `chunk_size` and each chunk is passed to `action` for
                treatment
            action (callable): Callable responsible of dealing with chunk of
                data
            chunk_size (int): Size of each chunk
            **kwargs: Extra options to send to the server (e.g. sudo)

        Raises:
            GitlabAuthenticationError: If authentication is not correct
            GitlabGetError: If the artifacts could not be retrieved

        Returns:
            str: The artifacts if `streamed` is False, None otherwise.
        """
        path = '%s/%s/artifacts/%s' % (self.manager.path, self.get_id(), path)
        result = self.manager.gitlab.http_get(path, streamed=streamed,
                                              raw=True, **kwargs)
        return utils.response_content(result, streamed, action, chunk_size)