def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(default='present', choices=['present', 'absent', 'revert', 'remove_all']),
        name=dict(required=True, type='str'),
        name_match=dict(type='str', default='first'),
        uuid=dict(type='str'),
        folder=dict(type='str', default='/vm'),
        datacenter=dict(required=True, type='str'),
        snapshot_name=dict(type='str'),
        description=dict(type='str', default=''),
        quiesce=dict(type='bool', default=False),
        memory_dump=dict(type='bool', default=False),
        remove_children=dict(type='bool', default=False),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    # Prepend /vm if it was missing from the folder path, also strip trailing slashes
    if not module.params['folder'].startswith('/vm') and module.params['folder'].startswith('/'):
        module.params['folder'] = '/vm%(folder)s' % module.params
    module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.getvm(name=module.params['name'],
                   folder=module.params['folder'],
                   uuid=module.params['uuid'])

    if not vm:
        # If UUID is set, getvm select UUID, show error message accordingly.
        if module.params['uuid'] is not None:
            module.fail_json(msg="Unable to manage snapshots for non-existing VM %(uuid)s" % module.params)
        else:
            module.fail_json(msg="Unable to manage snapshots for non-existing VM %(name)s" % module.params)

    if not module.params['snapshot_name'] and module.params['state'] != 'remove_all':
        module.fail_json(msg="snapshot_name param is required when state is '%(state)s'" % module.params)

    result = pyv.apply_snapshot_op(vm)

    if 'failed' not in result:
        result['failed'] = False

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)