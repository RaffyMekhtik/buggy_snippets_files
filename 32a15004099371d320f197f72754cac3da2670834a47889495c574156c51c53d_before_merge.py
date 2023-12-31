def mkfs(device, fs_type, **kwargs):
    '''
    Create a file system on the specified device

    CLI Example::

        salt '*' extfs.mkfs /dev/sda1 fs_type=ext4 opts='acl,noexec'

    Valid options are::

        block_size: 1024, 2048 or 4096
        check: check for bad blocks
        direct: use direct IO
        ext_opts: extended file system options (comma-separated)
        fragment_size: size of fragments
        force: setting force to True will cause mke2fs to specify the -F option
               twice (it is already set once); this is truly dangerous
        blocks_per_group: number of blocks in a block group
        number_of_groups: ext4 option for a virtual block group
        bytes_per_inode: set the bytes/inode ratio
        inode_size: size of the inode
        journal: set to True to create a journal (default on ext3/4)
        journal_opts: options for the fs journal (comma separated)
        blocks_file: read bad blocks from file
        label: label to apply to the file system
        reserved: percentage of blocks reserved for super-user
        last_dir: last mounted directory
        test: set to True to not actually create the file system (mke2fs -n)
        number_of_inodes: override default number of inodes
        creator_os: override "creator operating system" field
        opts: mount options (comma separated)
        revision: set the filesystem revision (default 1)
        super: write superblock and group descriptors only
        fs_type: set the filesystem type (REQUIRED)
        usage_type: how the filesystem is going to be used
        uuid: set the UUID for the file system

        see man 8 mke2fs for a more complete description of these options
    '''
    kwarg_map = {'block_size': 'b',
                 'check': 'c',
                 'direct': 'D',
                 'ext_opts': 'E',
                 'fragment_size': 'f',
                 'force': 'F',
                 'blocks_per_group': 'g',
                 'number_of_groups': 'G',
                 'bytes_per_inode': 'i',
                 'inode_size': 'I',
                 'journal': 'j',
                 'journal_opts': 'J',
                 'blocks_file': 'l',
                 'label': 'L',
                 'reserved': 'm',
                 'last_dir': 'M',
                 'test': 'n',
                 'number_of_inodes': 'N',
                 'creator_os': 'o',
                 'opts': 'O',
                 'revision': 'r',
                 'super': 'S',
                 'usage_type': 'T',
                 'uuid': 'U'}

    opts = ''
    for key in kwargs.keys():
        opt = kwarg_map[key]
        if kwargs[key] == 'True':
            opts += '-{0} '.format(opt)
        else:
            opts += '-{0} {1} '.format(opt, kwargs[key])
    cmd = 'mke2fs -F -t {0} {1}{2}'.format(fs_type, opts, device)
    out = __salt__['cmd.run'](cmd).splitlines()
    ret = []
    for line in out:
        if not line:
            continue
        elif line.startswith('mke2fs'):
            continue
        elif line.startswith('Discarding device blocks'):
            continue
        elif line.startswith('Allocating group tables'):
            continue
        elif line.startswith('Writing inode tables'):
            continue
        elif line.startswith('Creating journal'):
            continue
        elif line.startswith('Writing superblocks'):
            continue
        ret.append(line)
    return ret