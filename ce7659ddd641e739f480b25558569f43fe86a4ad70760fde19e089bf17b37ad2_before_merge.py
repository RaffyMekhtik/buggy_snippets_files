def absent(name, acl_type, acl_name='', perms='', recurse=False):
    '''
    Ensure a Linux ACL does not exist
    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    __current_perms = __salt__['acl.getfacl'](name)

    if acl_type.startswith(('d:', 'default:')):
        _acl_type = ':'.join(acl_type.split(':')[1:])
        _current_perms = __current_perms[name].get('defaults', {})
        _default = True
    else:
        _acl_type = acl_type
        _current_perms = __current_perms[name]
        _default = False

    # The getfacl execution module lists default with empty names as being
    # applied to the user/group that owns the file, e.g.,
    # default:group::rwx would be listed as default:group:root:rwx
    # In this case, if acl_name is empty, we really want to search for root

    # We search through the dictionary getfacl returns for the owner of the
    # file if acl_name is empty.
    if acl_name == '':
        _search_name = __current_perms[name].get('comment').get(_acl_type)
    else:
        _search_name = acl_name

    if _current_perms.get(_acl_type, None) or _default:
        try:
            user = [i for i in _current_perms[_acl_type] if next(six.iterkeys(i)) == _search_name].pop()
        except (AttributeError, IndexError, StopIteration, KeyError):
            user = None

        if user:
            ret['comment'] = 'Removing permissions'

            if __opts__['test']:
                ret['result'] = None
                return ret

            if recurse:
                __salt__['acl.delfacl'](acl_type, acl_name, perms, name, recursive=True)
            else:
                __salt__['acl.delfacl'](acl_type, acl_name, perms, name)
        else:
            ret['comment'] = 'Permissions are in the desired state'

    else:
        ret['comment'] = 'ACL Type does not exist'
        ret['result'] = False

    return ret