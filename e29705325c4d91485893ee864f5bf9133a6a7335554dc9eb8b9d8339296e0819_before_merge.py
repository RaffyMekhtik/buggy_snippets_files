def present(name,
           password=None,
           force=False,
           runas=None):
    '''
    Ensure the RabbitMQ user exists.

    name
        User name
    password
        User's password, if one needs to be set
    force
        If user exists, forcibly change the password
    runas
        Name of the user to run the command
    '''
    ret = {'name': name, 'result': True, 'comment': '', 'changes': {}}
    result = {}

    user_exists = __salt__['rabbitmq.user_exists'](name, runas=runas)

    if __opts__['test']:
        ret['result'] = None

        if not user_exists:
            ret['comment'] = 'User {0} is set to be created'
        elif force:
            ret['comment'] = 'User {0} is set to be updated'
        else:
            ret['comment'] = 'User {0} is not going to be modified'
        ret['comment'] = ret['comment'].format(name)
    else:
        if not user_exists:
            log.debug(
                "User doesn't exist - Creating")
            result = __salt__['rabbitmq.add_user'](
                name, password, runas=runas)
        elif force:
            log.debug('User exists and force is set - Overriding password')
            if password is not None:
                result = __salt__['rabbitmq.change_password'](
                    name, password, runas=runas)
            else:
                log.debug('Password is not set - Clearing password')
                result = __salt__['rabbitmq.clear_password'](
                    name, runas=runas)
        else:
            log.debug('User exists, and force is not set - Abandoning')
            ret['comment'] = 'User {0} is not going to be modified'.format(name)

        if 'Error' in result:
            ret['result'] = False
            ret['comment'] = result['Error']
        elif 'Added' in result:
            ret['comment'] = result['Added']
        elif 'Password Changed' in result:
            ret['comment'] = result['Password Changed']
        elif 'Password Cleared' in result:
            ret['comment'] = result['Password Cleared']

    return ret