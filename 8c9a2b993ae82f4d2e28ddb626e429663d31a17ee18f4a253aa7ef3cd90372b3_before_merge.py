def main():

    module = AnsibleModule(
        argument_spec=dict(
            component=dict(required=True, aliases=['name']),
            version=dict(required=True),
            token=dict(required=True, no_log=True),
            state=dict(required=True, choices=['started', 'finished', 'failed']),
            hosts=dict(required=False, default=[socket.gethostname()], aliases=['host']),
            env=dict(required=False),
            owner=dict(required=False),
            description=dict(required=False),
            message=dict(required=False),
            source_system=dict(required=False, default='ansible'),
            validate_certs=dict(default='yes', type='bool'),
            url=dict(required=False, default='https://api.bigpanda.io'),
        ),
        supports_check_mode=True,
    )

    token = module.params['token']
    state = module.params['state']
    url = module.params['url']

    # Build the common request body
    body = dict()
    for k in ('component', 'version', 'hosts'):
        v = module.params[k]
        if v is not None:
            body[k] = v

    if not isinstance(body['hosts'], list):
        body['hosts'] = [body['hosts']]

    # Insert state-specific attributes to body
    if state == 'started':
        for k in ('source_system', 'env', 'owner', 'description'):
            v = module.params[k]
            if v is not None:
                body[k] = v

        request_url = url + '/data/events/deployments/start'
    else:
        message = module.params['message']
        if message is not None:
            body['errorMessage'] = message

        if state == 'finished':
            body['status'] = 'success'
        else:
            body['status'] = 'failure'

        request_url = url + '/data/events/deployments/end'

    # Build the deployment object we return
    deployment = dict(token=token, url=url)
    deployment.update(body)
    if 'errorMessage' in deployment:
        message = deployment.pop('errorMessage')
        deployment['message'] = message

    # If we're in check mode, just exit pretending like we succeeded
    if module.check_mode:
        module.exit_json(changed=True, **deployment)

    # Send the data to bigpanda
    data = json.dumps(body)
    headers = {'Authorization': 'Bearer %s' % token, 'Content-Type': 'application/json'}
    try:
        response, info = fetch_url(module, request_url, data=data, headers=headers)
        if info['status'] == 200:
            module.exit_json(changed=True, **deployment)
        else:
            module.fail_json(msg=json.dumps(info))
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())