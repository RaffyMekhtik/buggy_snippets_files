def on_resource_changed(event):
    """
    Everytime an object is created/changed/deleted, we create an entry in the
    ``history`` resource. The entries are served as read-only in the
    :mod:`kinto.plugins.history.views` module.
    """
    payload = copy.deepcopy(event.payload)
    resource_name = payload['resource_name']
    event_uri = payload['uri']

    bucket_id = payload.pop('bucket_id')
    bucket_uri = instance_uri(event.request, 'bucket', id=bucket_id)
    collection_id = None
    collection_uri = None
    if 'collection_id' in payload:
        collection_id = payload['collection_id']
        collection_uri = instance_uri(event.request,
                                      'collection',
                                      bucket_id=bucket_id,
                                      id=collection_id)

    storage = event.request.registry.storage
    permission = event.request.registry.permission

    targets = []
    for impacted in event.impacted_records:
        # On POST .../records, the URI does not contain the newly created
        # record id.
        target = impacted['new']
        obj_id = target['id']
        parts = event_uri.split('/')
        if resource_name in parts[-1]:
            parts.append(obj_id)
        else:
            # Make sure the id is correct on grouped events.
            parts[-1] = obj_id
        uri = '/'.join(parts)
        targets.append((uri, target))

    # Prepare a list of object ids to be fetched from permission backend,
    # and fetch them all at once. Use a mapping for later convenience.
    all_perms_objects_ids = [oid for (oid, _) in targets]
    all_perms_objects_ids.append(bucket_uri)
    if collection_uri is not None:
        all_perms_objects_ids.append(collection_uri)
    all_perms_objects_ids = list(set(all_perms_objects_ids))
    all_permissions = permission.get_objects_permissions(all_perms_objects_ids)
    perms_by_object_id = dict(zip(all_perms_objects_ids, all_permissions))

    bucket_perms = perms_by_object_id[bucket_uri]
    collection_perms = {}
    if collection_uri is not None:
        collection_perms = perms_by_object_id[collection_uri]

    # The principals allowed to read the bucket and collection.
    # (Note: ``write`` means ``read``)
    read_principals = set(bucket_perms.get('read', []))
    read_principals.update(bucket_perms.get('write', []))
    read_principals.update(collection_perms.get('read', []))
    read_principals.update(collection_perms.get('write', []))

    # Create a history entry for each impacted record.
    for (uri, target) in targets:
        obj_id = target['id']
        # Prepare the history entry attributes.
        perms = {k: list(v) for k, v in perms_by_object_id[uri].items()}
        eventattrs = dict(**payload)
        eventattrs.setdefault('%s_id' % resource_name, obj_id)
        eventattrs['uri'] = uri
        attrs = dict(date=datetime.now().isoformat(),
                     target={'data': target, 'permissions': perms},
                     **eventattrs)

        # Create a record for the 'history' resource, whose parent_id is
        # the bucket URI (c.f. views.py).
        # Note: this will be rolledback if the transaction is rolledback.
        entry = storage.create(parent_id=bucket_uri,
                               collection_id='history',
                               record=attrs)

        # The read permission on the newly created history entry is the union
        # of the record permissions with the one from bucket and collection.
        entry_principals = set(read_principals)
        entry_principals.update(perms.get('read', []))
        entry_principals.update(perms.get('write', []))
        entry_perms = {'read': list(entry_principals)}
        # /buckets/{id}/history is the URI for the list of history entries.
        entry_perm_id = '/buckets/%s/history/%s' % (bucket_id, entry['id'])
        permission.replace_object_permissions(entry_perm_id, entry_perms)