  def Do(self, input_dict: Dict[Text, List[types.Artifact]],
         output_dict: Dict[Text, List[types.Artifact]],
         exec_properties: Dict[Text, Any]):
    """Overrides the tfx_pusher_executor.

    Args:
      input_dict: Input dict from input key to a list of artifacts, including:
        - model_export: exported model from trainer.
        - model_blessing: model blessing path from model_validator.
      output_dict: Output dict from key to a list of artifacts, including:
        - model_push: A list of 'ModelPushPath' artifact of size one. It will
          include the model in this push execution if the model was pushed.
      exec_properties: Mostly a passthrough input dict for
        tfx.components.Pusher.executor.  custom_config.ai_platform_serving_args
        is consumed by this class.  For the full set of parameters supported by
        Google Cloud AI Platform, refer to
        https://cloud.google.com/ml-engine/docs/tensorflow/deploying-models#creating_a_model_version.

    Raises:
      ValueError:
        If ai_platform_serving_args is not in exec_properties.custom_config.
        If Serving model path does not start with gs://.
      RuntimeError: if the Google Cloud AI Platform training job failed.
    """
    self._log_startup(input_dict, output_dict, exec_properties)
    model_push = artifact_utils.get_single_instance(
        output_dict[tfx_pusher_executor.PUSHED_MODEL_KEY])
    if not self.CheckBlessing(input_dict):
      self._MarkNotPushed(model_push)
      return

    model_export = artifact_utils.get_single_instance(
        input_dict[tfx_pusher_executor.MODEL_KEY])

    exec_properties_copy = exec_properties.copy()
    custom_config = exec_properties_copy.pop(_CUSTOM_CONFIG_KEY, {})
    ai_platform_serving_args = custom_config.get(SERVING_ARGS_KEY)
    if not ai_platform_serving_args:
      raise ValueError(
          '\'ai_platform_serving_args\' is missing in \'custom_config\'')
    # Deploy the model.
    io_utils.copy_dir(
        src=path_utils.serving_model_path(model_export.uri),
        dst=model_push.uri)
    model_path = model_push.uri
    # TODO(jjong): Introduce Versioning.
    # Note that we're adding "v" prefix as Cloud AI Prediction only allows the
    # version name that starts with letters, and contains letters, digits,
    # underscore only.
    model_version = 'v{}'.format(int(time.time()))
    executor_class_path = '%s.%s' % (self.__class__.__module__,
                                     self.__class__.__name__)
    runner.deploy_model_for_aip_prediction(
        model_path,
        model_version,
        ai_platform_serving_args,
        executor_class_path,
    )

    self._MarkPushed(
        model_push,
        pushed_destination=_CAIP_MODEL_VERSION_PATH_FORMAT.format(
            project_id=ai_platform_serving_args['project_id'],
            model=ai_platform_serving_args['model_name'],
            version=model_version),
        pushed_version=model_version)