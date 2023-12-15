    def run(self):
        if "__PEX_UNVENDORED__" in __import__("os").environ:
          import setuptools.command.easy_install as ei  # vendor:skip
        else:
          import pex.third_party.setuptools.command.easy_install as ei


        self.run_command("egg_info")
        if self.distribution.scripts:
            orig.install_scripts.run(self)  # run first to set up self.outfiles
        else:
            self.outfiles = []
        if self.no_ep:
            # don't install entry point scripts into .egg file!
            return

        ei_cmd = self.get_finalized_command("egg_info")
        dist = Distribution(
            ei_cmd.egg_base, PathMetadata(ei_cmd.egg_base, ei_cmd.egg_info),
            ei_cmd.egg_name, ei_cmd.egg_version,
        )
        bs_cmd = self.get_finalized_command('build_scripts')
        exec_param = getattr(bs_cmd, 'executable', None)
        bw_cmd = self.get_finalized_command("bdist_wininst")
        is_wininst = getattr(bw_cmd, '_is_running', False)
        writer = ei.ScriptWriter
        if is_wininst:
            exec_param = "python.exe"
            writer = ei.WindowsScriptWriter
        if exec_param == sys.executable:
            # In case the path to the Python executable contains a space, wrap
            # it so it's not split up.
            exec_param = [exec_param]
        # resolve the writer to the environment
        writer = writer.best()
        cmd = writer.command_spec_class.best().from_param(exec_param)
        for args in writer.get_args(dist, cmd.as_header()):
            self.write_script(*args)