def check_gpus_data_type(gpus):
    """
    :param gpus: gpus parameter as passed to the Trainer
        Function checks that it is one of: None, Int, String or List
        Throws otherwise
    :return: return unmodified gpus variable
    """

    if gpus is not None and type(gpus) not in (int, str, list):
        raise MisconfigurationException("GPUs must be int, string or list of ints or None.")