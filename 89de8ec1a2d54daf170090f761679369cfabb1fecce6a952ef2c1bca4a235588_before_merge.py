    def on_files_excluded(self, files_data):
        included_list = self.get_included_file_list()
        for file_data in files_data:
            if file_data["index"] in included_list:
                included_list.remove(file_data["index"])

        self.set_included_files(included_list)