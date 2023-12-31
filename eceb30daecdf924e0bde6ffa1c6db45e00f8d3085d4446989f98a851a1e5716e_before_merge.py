def get_resource_tags(resource_type, entity_config):
    if '_' not in resource_type:
        return None  # probably not a resource block
    provider = resource_type[:resource_type.index('_')]
    provider_tag_function = provider_tag_mapping.get(provider)
    if provider_tag_function:
        return provider_tag_function(entity_config)
    else:
        return None