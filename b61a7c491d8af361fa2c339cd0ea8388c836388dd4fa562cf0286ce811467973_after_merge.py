def build_torch_policy(name,
                       loss_fn,
                       get_default_config=None,
                       stats_fn=None,
                       postprocess_fn=None,
                       extra_action_out_fn=None,
                       extra_grad_process_fn=None,
                       optimizer_fn=None,
                       before_init=None,
                       after_init=None,
                       make_model_and_action_dist=None,
                       mixins=None):
    """Helper function for creating a torch policy at runtime.

    Arguments:
        name (str): name of the policy (e.g., "PPOTorchPolicy")
        loss_fn (func): function that returns a loss tensor as arguments
            (policy, model, dist_class, train_batch)
        get_default_config (func): optional function that returns the default
            config to merge with any overrides
        stats_fn (func): optional function that returns a dict of
            values given the policy and batch input tensors
        postprocess_fn (func): optional experience postprocessing function
            that takes the same args as Policy.postprocess_trajectory()
        extra_action_out_fn (func): optional function that returns
            a dict of extra values to include in experiences
        extra_grad_process_fn (func): optional function that is called after
            gradients are computed and returns processing info
        optimizer_fn (func): optional function that returns a torch optimizer
            given the policy and config
        before_init (func): optional function to run at the beginning of
            policy init that takes the same arguments as the policy constructor
        after_init (func): optional function to run at the end of policy init
            that takes the same arguments as the policy constructor
        make_model_and_action_dist (func): optional func that takes the same
            arguments as policy init and returns a tuple of model instance and
            torch action distribution class. If not specified, the default
            model and action dist from the catalog will be used
        mixins (list): list of any class mixins for the returned policy class.
            These mixins will be applied in order and will have higher
            precedence than the TorchPolicy class

    Returns:
        a TorchPolicy instance that uses the specified args
    """

    original_kwargs = locals().copy()
    base = add_mixins(TorchPolicy, mixins)

    class policy_cls(base):
        def __init__(self, obs_space, action_space, config):
            if get_default_config:
                config = dict(get_default_config(), **config)
            self.config = config

            if before_init:
                before_init(self, obs_space, action_space, config)

            if make_model_and_action_dist:
                self.model, self.dist_class = make_model_and_action_dist(
                    self, obs_space, action_space, config)
                # Make sure, we passed in a correct Model factory.
                assert isinstance(self.model, TorchModelV2), \
                    "ERROR: TorchPolicy::make_model_and_action_dist must " \
                    "return a TorchModelV2 object!"
            else:
                self.dist_class, logit_dim = ModelCatalog.get_action_dist(
                    action_space, self.config["model"], framework="torch")
                self.model = ModelCatalog.get_model_v2(
                    obs_space,
                    action_space,
                    logit_dim,
                    self.config["model"],
                    framework="torch")

            TorchPolicy.__init__(
                self, obs_space, action_space, config, self.model,
                loss_fn, self.dist_class
            )

            if after_init:
                after_init(self, obs_space, action_space, config)

        @override(Policy)
        def postprocess_trajectory(self,
                                   sample_batch,
                                   other_agent_batches=None,
                                   episode=None):
            if not postprocess_fn:
                return sample_batch

            # Do all post-processing always with no_grad().
            # Not using this here will introduce a memory leak (issue #6962).
            with torch.no_grad():
                return postprocess_fn(
                    self, convert_to_non_torch_type(sample_batch),
                    convert_to_non_torch_type(other_agent_batches), episode)

        @override(TorchPolicy)
        def extra_grad_process(self):
            if extra_grad_process_fn:
                return extra_grad_process_fn(self)
            else:
                return TorchPolicy.extra_grad_process(self)

        @override(TorchPolicy)
        def extra_action_out(self, input_dict, state_batches, model,
                             action_dist=None):
            with torch.no_grad():
                if extra_action_out_fn:
                    stats_dict = extra_action_out_fn(
                        self, input_dict, state_batches, model, action_dist
                    )
                else:
                    stats_dict = TorchPolicy.extra_action_out(
                        self, input_dict, state_batches, model, action_dist
                    )
                return convert_to_non_torch_type(stats_dict)

        @override(TorchPolicy)
        def optimizer(self):
            if optimizer_fn:
                return optimizer_fn(self, self.config)
            else:
                return TorchPolicy.optimizer(self)

        @override(TorchPolicy)
        def extra_grad_info(self, train_batch):
            with torch.no_grad():
                if stats_fn:
                    stats_dict = stats_fn(self, train_batch)
                else:
                    stats_dict = TorchPolicy.extra_grad_info(self, train_batch)
                return convert_to_non_torch_type(stats_dict)

    def with_updates(**overrides):
        return build_torch_policy(**dict(original_kwargs, **overrides))

    policy_cls.with_updates = staticmethod(with_updates)
    policy_cls.__name__ = name
    policy_cls.__qualname__ = name
    return policy_cls