    def inventory(self, cache: snakemake.io.IOCache):
        """Using client.list_blobs(), we want to iterate over the objects in
           the "folder" of a bucket and store information about the IOFiles in the
           provided cache (snakemake.io.IOCache) indexed by bucket/blob name.
           This will be called by the first mention of a remote object, and
           iterate over the entire bucket once (and then not need to again). 
           This includes:
            - cache.exist_remote
            - cache_mtime
            - cache.size
        """
        subfolder = os.path.dirname(self.blob.name)
        for blob in self.client.list_blobs(self.bucket_name, prefix=subfolder):
            # By way of being listed, it exists. mtime is a datetime object
            name = "{}/{}".format(blob.bucket.name, blob.name)
            cache.exists_remote[name] = True
            cache.mtime[name] = blob.updated
            cache.size[name] = blob.size

        # Mark bucket and prefix as having an inventory, such that this method is
        # only called once for the subfolder in the bucket.
        cache.has_inventory.add("%s/%s" % (self.bucket_name, subfolder))