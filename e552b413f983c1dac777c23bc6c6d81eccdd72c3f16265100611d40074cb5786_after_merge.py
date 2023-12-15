    def transition_coeff(
        self, feature: Tensor  # (batch_size, time_length, 1)
    ) -> Tensor:
        F = getF(feature)

        _transition_coeff = (
            (F.diag(F.ones(shape=(2,)), k=0) + F.diag(F.ones(shape=(1,)), k=1))
            .expand_dims(axis=0)
            .expand_dims(axis=0)
        )

        # get the right shape: (batch_size, time_length, latent_dim, latent_dim)
        zeros = _broadcast_param(
            feature.squeeze(axis=2),
            axes=[2, 3],
            sizes=[self.latent_dim(), self.latent_dim()],
        )

        return _transition_coeff.broadcast_like(zeros)