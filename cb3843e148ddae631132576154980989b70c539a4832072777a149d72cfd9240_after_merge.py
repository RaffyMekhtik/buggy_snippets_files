def infer(features_file,
          estimator,
          model,
          config,
          checkpoint_path=None,
          predictions_file=None):
  """Runs inference and prints predictions on the standard output.

  Args:
    features_file: The file to infer from.
    estimator: A `tf.estimator.Estimator`.
    model: A `opennmt.models.Model`.
    config: The configuration.
    checkpoint_path: Path of a specific checkpoint to predict. If `None`, the
      latest is used.
    predictions_file: If set, predictions are saved in this file.
  """
  if "infer" not in config:
    config["infer"] = {}

  batch_size = config["infer"].get("batch_size", 1)
  input_fn = model.input_fn(
      tf.estimator.ModeKeys.PREDICT,
      batch_size,
      config["infer"].get("buffer_size", batch_size * 10),
      config["infer"].get("num_parallel_process_calls", multiprocessing.cpu_count()),
      config["data"],
      features_file)

  if predictions_file:
    stream = open(predictions_file, "w")
  else:
    stream = sys.stdout

  for prediction in estimator.predict(input_fn=input_fn, checkpoint_path=checkpoint_path):
    model.print_prediction(prediction, params=config["infer"], stream=stream)

  if predictions_file:
    stream.close()