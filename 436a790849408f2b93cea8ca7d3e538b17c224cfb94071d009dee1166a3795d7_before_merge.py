def role_spec_parse(role_spec):
    # takes a repo and a version like
    # git+http://git.example.com/repos/repo.git,v1.0
    # and returns a list of properties such as:
    # {
    #   'scm': 'git',
    #   'src': 'http://git.example.com/repos/repo.git',
    #   'version': 'v1.0',
    #   'name': 'repo'
    # }

    default_role_versions = dict(git='master', hg='tip')

    role_spec = role_spec.strip()
    role_version = ''
    if role_spec == "" or role_spec.startswith("#"):
        return (None, None, None, None)

    tokens = [s.strip() for s in role_spec.split(',')]

    # assume https://github.com URLs are git+https:// URLs and not
    # tarballs unless they end in '.zip'
    if 'github.com/' in tokens[0] and not tokens[0].startswith("git+") and not tokens[0].endswith('.tar.gz'):
        tokens[0] = 'git+' + tokens[0]

    if '+' in tokens[0]:
        (scm, role_url) = tokens[0].split('+')
    else:
        scm = None
        role_url = tokens[0]

    if len(tokens) >= 2:
        role_version = tokens[1]

    if len(tokens) == 3:
        role_name = tokens[2]
    else:
        role_name = repo_url_to_role_name(tokens[0])

    if scm and not role_version:
        role_version = default_role_versions.get(scm, '')

    return dict(scm=scm, src=role_url, version=role_version, role_name=role_name)