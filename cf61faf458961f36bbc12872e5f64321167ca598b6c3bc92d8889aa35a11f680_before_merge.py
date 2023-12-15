    def checkout_exp(self, rev, allow_missing=False):
        """Checkout an experiment to the user's workspace."""
        from git.exc import GitCommandError

        from dvc.repo.checkout import checkout as dvc_checkout

        baseline_rev = self._check_baseline(rev)
        self._scm_checkout(rev)

        tmp = tempfile.NamedTemporaryFile(delete=False).name
        self.scm.repo.head.commit.diff(
            baseline_rev, patch=True, full_index=True, binary=True, output=tmp
        )

        dirty = self.repo.scm.is_dirty()
        if dirty:
            logger.debug("Stashing workspace changes.")
            self.repo.scm.repo.git.stash("push", "--include-untracked")

        try:
            if os.path.getsize(tmp):
                logger.debug("Patching local workspace")
                self.repo.scm.repo.git.apply(tmp, reverse=True)
                need_checkout = True
            else:
                need_checkout = False
        except GitCommandError:
            raise DvcException("failed to apply experiment changes.")
        finally:
            remove(tmp)
            if dirty:
                self._unstash_workspace()

        if need_checkout:
            dvc_checkout(self.repo, allow_missing=allow_missing)