def __dict_to_object_meta(name, namespace, metadata):
    '''
    Converts a dictionary into kubernetes ObjectMetaV1 instance.
    '''
    meta_obj = kubernetes.client.V1ObjectMeta()
    meta_obj.namespace = namespace
    for key, value in iteritems(metadata):
        if hasattr(meta_obj, key):
            setattr(meta_obj, key, value)

    if meta_obj.name != name:
        log.warning(
            'The object already has a name attribute, overwriting it with '
            'the one defined inside of salt')
        meta_obj.name = name

    return meta_obj