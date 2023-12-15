    def load_data(self, filename, ext):
        if self._reading:
            message = _("Loading this kind of data while debugging is not "
                        "supported.")
            QMessageBox.warning(self, _("Warning"), message)
            return
        # Wait until the kernel tries to load the file
        wait_loop = QEventLoop()
        self.sig_got_reply.connect(wait_loop.quit)
        self.silent_exec_method(
                r"get_ipython().kernel.load_data('%s', '%s')" % (filename, ext))
        wait_loop.exec_()

        # Remove loop connection and loop
        self.sig_got_reply.disconnect(wait_loop.quit)
        wait_loop = None

        return self._kernel_reply