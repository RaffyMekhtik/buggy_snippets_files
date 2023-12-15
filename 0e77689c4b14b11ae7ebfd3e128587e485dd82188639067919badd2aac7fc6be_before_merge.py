    def __init__(self, galaxy, name, src=None, version=None, scm=None, role_path=None):

        self._metadata = None
        self._install_info = None

        self.options = galaxy.options

        self.name = name
        self.version = version
        self.src = src or name
        self.scm = scm

        if role_path is not None:
            self.path = role_path
        else:
            for path in galaxy.roles_paths:
                role_path = os.path.join(path, self.name)
                if os.path.exists(role_path):
                    self.path = role_path
                    break
            else:
                # use the first path by default
                self.path = os.path.join(galaxy.roles_paths[0], self.name)