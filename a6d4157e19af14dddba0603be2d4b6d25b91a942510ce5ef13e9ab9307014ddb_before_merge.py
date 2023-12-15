            def process_csv_row(row):
                cleaned_path = posix_normpath("%s%s%s" % (sp_dir, path_prepender, row[0]))
                if len(row) == 3:
                    checksum, size = row[1:]
                    if checksum:
                        assert checksum.startswith('sha256='), (self._metadata_dir_full_path,
                                                                cleaned_path, checksum)
                        checksum = checksum[7:]
                    else:
                        checksum = None
                    size = int(size) if size else None
                else:
                    checksum = size = None
                return cleaned_path, checksum, size