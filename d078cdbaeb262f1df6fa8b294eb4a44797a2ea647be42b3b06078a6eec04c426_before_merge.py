def hash_file(path, hashobj, conn=None):
    '''
    Get the hexdigest hash value of a file
    '''
    if os.path.isdir(path):
        return ''

    with salt.utils.fopen(path, 'r') as f:
        hashobj.update(f.read())
        return hashobj.hexdigest()