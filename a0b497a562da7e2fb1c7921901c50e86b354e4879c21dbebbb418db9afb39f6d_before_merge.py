  def ParseOptions(cls, options, analysis_plugin):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      analysis_plugin (ViperAnalysisPlugin): analysis plugin to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
    """
    if not isinstance(analysis_plugin, viper.ViperAnalysisPlugin):
      raise errors.BadConfigObject(
          u'Analysis plugin is not an instance of ViperAnalysisPlugin')

    host = cls._ParseStringOption(
        options, u'viper_host', default_value=cls._DEFAULT_HOST)
    analysis_plugin.SetHost(host)

    protocol = cls._ParseStringOption(
        options, u'viper_protocol', default_value=cls._DEFAULT_PROTOCOL)
    analysis_plugin.SetProtocol(protocol)