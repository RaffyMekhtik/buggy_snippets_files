    def scan_fortran_module_outputs(self, target):
        compiler = None
        for lang, c in self.build.compilers.items():
            if lang == 'fortran':
                compiler = c
                break
        if compiler is None:
            self.fortran_deps[target.get_basename()] = {}
            return
        modre = re.compile(r"\s*module\s+(\w+)", re.IGNORECASE)
        module_files = {}
        for s in target.get_sources():
            # FIXME, does not work for Fortran sources generated by
            # custom_target() and generator() as those are run after
            # the configuration (configure_file() is OK)
            if not compiler.can_compile(s):
                continue
            filename = s.absolute_path(self.environment.get_source_dir(),
                                       self.environment.get_build_dir())
            with open(filename) as f:
                for line in f:
                    modmatch = modre.match(line)
                    if modmatch is not None:
                        modname = modmatch.group(1)
                        if modname.lower() == 'procedure':
                            # MODULE PROCEDURE construct
                            continue
                        if modname in module_files:
                            raise InvalidArguments(
                                'Namespace collision: module %s defined in '
                                'two files %s and %s.' %
                                (modname, module_files[modname], s))
                        module_files[modname] = s
        self.fortran_deps[target.get_basename()] = module_files