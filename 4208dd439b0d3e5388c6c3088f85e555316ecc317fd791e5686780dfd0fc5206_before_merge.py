    def fit(self, X, y=None):
        """Fit the hierarchical clustering from features, or distance matrix.

        Parameters
        ----------
        X : array-like, shape (n_samples, n_features) or (n_samples, n_samples)
            Training instances to cluster, or distances between instances if
            ``affinity='precomputed'``.

        y : Ignored
            Not used, present here for API consistency by convention.

        Returns
        -------
        self
        """
        X = self._validate_data(X, ensure_min_samples=2, estimator=self)
        memory = check_memory(self.memory)

        if self.n_clusters is not None and self.n_clusters <= 0:
            raise ValueError("n_clusters should be an integer greater than 0."
                             " %s was provided." % str(self.n_clusters))

        if not ((self.n_clusters is None) ^ (self.distance_threshold is None)):
            raise ValueError("Exactly one of n_clusters and "
                             "distance_threshold has to be set, and the other "
                             "needs to be None.")

        if (self.distance_threshold is not None
                and not self.compute_full_tree):
            raise ValueError("compute_full_tree must be True if "
                             "distance_threshold is set.")

        if self.linkage == "ward" and self.affinity != "euclidean":
            raise ValueError("%s was provided as affinity. Ward can only "
                             "work with euclidean distances." %
                             (self.affinity, ))

        if self.linkage not in _TREE_BUILDERS:
            raise ValueError("Unknown linkage type %s. "
                             "Valid options are %s" % (self.linkage,
                                                       _TREE_BUILDERS.keys()))
        tree_builder = _TREE_BUILDERS[self.linkage]

        connectivity = self.connectivity
        if self.connectivity is not None:
            if callable(self.connectivity):
                connectivity = self.connectivity(X)
            connectivity = check_array(
                connectivity, accept_sparse=['csr', 'coo', 'lil'])

        n_samples = len(X)
        compute_full_tree = self.compute_full_tree
        if self.connectivity is None:
            compute_full_tree = True
        if compute_full_tree == 'auto':
            if self.distance_threshold is not None:
                compute_full_tree = True
            else:
                # Early stopping is likely to give a speed up only for
                # a large number of clusters. The actual threshold
                # implemented here is heuristic
                compute_full_tree = self.n_clusters < max(100, .02 * n_samples)
        n_clusters = self.n_clusters
        if compute_full_tree:
            n_clusters = None

        # Construct the tree
        kwargs = {}
        if self.linkage != 'ward':
            kwargs['linkage'] = self.linkage
            kwargs['affinity'] = self.affinity

        distance_threshold = self.distance_threshold

        return_distance = distance_threshold is not None
        out = memory.cache(tree_builder)(X, connectivity=connectivity,
                                         n_clusters=n_clusters,
                                         return_distance=return_distance,
                                         **kwargs)
        (self.children_,
         self.n_connected_components_,
         self.n_leaves_,
         parents) = out[:4]

        if return_distance:
            self.distances_ = out[-1]
            self.n_clusters_ = np.count_nonzero(
                self.distances_ >= distance_threshold) + 1
        else:
            self.n_clusters_ = self.n_clusters

        # Cut the tree
        if compute_full_tree:
            self.labels_ = _hc_cut(self.n_clusters_, self.children_,
                                   self.n_leaves_)
        else:
            labels = _hierarchical.hc_get_heads(parents, copy=False)
            # copy to avoid holding a reference on the original array
            labels = np.copy(labels[:n_samples])
            # Reassign cluster numbers
            self.labels_ = np.searchsorted(np.unique(labels), labels)
        return self