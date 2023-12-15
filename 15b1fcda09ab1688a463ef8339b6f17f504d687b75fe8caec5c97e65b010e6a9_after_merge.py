    def on_create_clicked(self):
        if self.window().create_torrent_files_list.count() == 0:
            self.dialog = ConfirmationDialog(self, "Notice", "You should add at least one file to your torrent.",
                                             [('CLOSE', BUTTON_TYPE_NORMAL)])
            self.dialog.button_clicked.connect(self.on_dialog_ok_clicked)
            self.dialog.show()
            return

        files_str = u""
        for ind in xrange(self.window().create_torrent_files_list.count()):
            files_str += u"files[]=%s&" % urllib.quote_plus(
                self.window().create_torrent_files_list.item(ind).text().encode('utf-8'))

        name = urllib.quote_plus(self.window().create_torrent_name_field.text().encode('utf-8'))
        description = urllib.quote_plus(self.window().create_torrent_description_field.toPlainText().encode('utf-8'))
        post_data = (u"%s&name=%s&description=%s" % (files_str[:-1], name, description)).encode('utf-8')
        url = "createtorrent?download=1" if self.window().seed_after_adding_checkbox.isChecked() else "createtorrent"
        self.request_mgr = TriblerRequestManager()
        self.request_mgr.perform_request(url, self.on_torrent_created, data=post_data, method='POST')
        # Show creating torrent text
        self.window().edit_channel_create_torrent_progress_label.show()