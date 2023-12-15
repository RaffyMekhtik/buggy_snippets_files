def list_input_endpoints(kwargs=None, conn=None, call=None):
    '''
    .. versionadded:: 2015.8.0

    List input endpoints associated with the deployment

    CLI Example:

    .. code-block:: bash

        salt-cloud -f list_input_endpoints my-azure service=myservice deployment=mydeployment
    '''
    if call != 'function':
        raise SaltCloudSystemExit(
            'The list_input_endpoints function must be called with -f or --function.'
        )

    if kwargs is None:
        kwargs = {}

    if 'service' not in kwargs:
        raise SaltCloudSystemExit('A service name must be specified as "service"')

    if 'deployment' not in kwargs:
        raise SaltCloudSystemExit('A deployment name must be specified as "deployment"')

    path = 'services/hostedservices/{0}/deployments/{1}'.format(
        kwargs['service'],
        kwargs['deployment'],
    )

    data = query(path)
    if data is None:
        raise SaltCloudSystemExit(
            'There was an error listing endpoints with the {0} service on the {1} deployment.'.format(
                kwargs['service'],
                kwargs['deployment']
            )
        )

    ret = {}
    for item in data:
        if 'Role' not in item:
            continue
        for role in item['Role']:
            input_endpoint = role['ConfigurationSets']['ConfigurationSet'].get('InputEndpoints', {}).get('InputEndpoint')
            if not input_endpoint:
                continue
            if not isinstance(input_endpoint, list):
                input_endpoint = [input_endpoint]
            for endpoint in input_endpoint:
                ret[endpoint['Name']] = endpoint
    return ret