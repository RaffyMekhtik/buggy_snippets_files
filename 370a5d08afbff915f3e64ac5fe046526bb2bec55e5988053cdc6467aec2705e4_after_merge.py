def present(name, database, duration="7d",
            replication=1, default=False,
            **client_args):
    '''
    Ensure that given retention policy is present.

    name
        Name of the retention policy to create.

    database
        Database to create retention policy on.
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'retention policy {0} is already present'.format(name)}

    if not __salt__['influxdb.retention_policy_exists'](name=name,
                                                        database=database,
                                                        **client_args):
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = ' {0} is absent and will be created'\
                .format(name)
            return ret
        if __salt__['influxdb.create_retention_policy'](
            database, name,
            duration, replication, default, **client_args
        ):
            ret['comment'] = 'retention policy {0} has been created'\
                .format(name)
            ret['changes'][name] = 'Present'
            return ret
        else:
            ret['comment'] = 'Failed to create retention policy {0}'\
                .format(name)
            ret['result'] = False
            return ret

    else:
        current_policy = __salt__['influxdb.get_retention_policy'](database=database, name=name, **client_args)
        update_policy = False
        if current_policy['duration'] != convert_duration(duration):
            update_policy = True
            ret['changes']['duration'] = "Retention changed from {0} to {1}.".format(current_policy['duration'], duration)

        if current_policy['replicaN'] != replication:
            update_policy = True
            ret['changes']['replication'] = "Replication changed from {0} to {1}.".format(current_policy['replicaN'], replication)

        if current_policy['default'] != default:
            update_policy = True
            ret['changes']['default'] = "Default changed from {0} to {1}.".format(current_policy['default'], default)

        if update_policy:
            if __opts__['test']:
                ret['result'] = None
                ret['comment'] = ' {0} is present and set to be changed'\
                    .format(name)
                return ret
            else:
                if __salt__['influxdb.alter_retention_policy'](
                    database, name,
                    duration, replication, default, **client_args
                ):
                    ret['comment'] = 'retention policy {0} has been changed'\
                        .format(name)
                    return ret
                else:
                    ret['comment'] = 'Failed to update retention policy {0}'\
                        .format(name)
                    ret['result'] = False
                    return ret

    return ret