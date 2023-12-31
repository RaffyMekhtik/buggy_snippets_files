def get_files_to_transfer(channel_id, node_ids, exclude_node_ids, available):
    files_to_transfer = LocalFile.objects.filter(files__contentnode__channel_id=channel_id, available=available)

    if node_ids:
        leaf_node_ids = _get_leaf_node_ids(node_ids)
        files_to_transfer = files_to_transfer.filter(files__contentnode__in=leaf_node_ids)

    if exclude_node_ids:
        exclude_leaf_node_ids = _get_leaf_node_ids(exclude_node_ids)
        files_to_transfer = files_to_transfer.exclude(files__contentnode__in=exclude_leaf_node_ids)

    # Make sure the files are unique, to avoid duplicating downloads
    files_to_transfer = files_to_transfer.distinct()

    total_bytes_to_transfer = files_to_transfer.aggregate(Sum('file_size'))['file_size__sum'] or 0

    return files_to_transfer, total_bytes_to_transfer