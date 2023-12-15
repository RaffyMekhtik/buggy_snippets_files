    def define_routes(self):
        """
        The web app routes for sharing files
        """

        @self.web.app.route("/", defaults={"path": ""})
        @self.web.app.route("/<path:path>")
        def index(path):
            """
            Render the template for the onionshare landing page.
            """
            self.web.add_request(self.web.REQUEST_LOAD, request.path)

            # Deny new downloads if "Stop sharing after files have been sent" is checked and there is
            # currently a download
            deny_download = (
                self.web.settings.get("share", "autostop_sharing")
                and self.download_in_progress
            )
            if deny_download:
                r = make_response(render_template("denied.html"))
                return self.web.add_security_headers(r)

            # If download is allowed to continue, serve download page
            if self.should_use_gzip():
                self.filesize = self.gzip_filesize
            else:
                self.filesize = self.download_filesize

            return self.render_logic(path)

        @self.web.app.route("/download")
        def download():
            """
            Download the zip file.
            """
            # Deny new downloads if "Stop After First Download" is checked and there is
            # currently a download
            deny_download = (
                self.web.settings.get("share", "autostop_sharing")
                and self.download_in_progress
            )
            if deny_download:
                r = make_response(render_template("denied.html"))
                return self.web.add_security_headers(r)

            # Prepare some variables to use inside generate() function below
            # which is outside of the request context
            shutdown_func = request.environ.get("werkzeug.server.shutdown")
            path = request.path

            # If this is a zipped file, then serve as-is. If it's not zipped, then,
            # if the http client supports gzip compression, gzip the file first
            # and serve that
            use_gzip = self.should_use_gzip()
            if use_gzip:
                file_to_download = self.gzip_filename
                self.filesize = self.gzip_filesize
            else:
                file_to_download = self.download_filename
                self.filesize = self.download_filesize

            # Tell GUI the download started
            history_id = self.cur_history_id
            self.cur_history_id += 1
            self.web.add_request(
                self.web.REQUEST_STARTED, path, {"id": history_id, "use_gzip": use_gzip}
            )

            basename = os.path.basename(self.download_filename)

            def generate():
                # Starting a new download
                if self.web.settings.get("share", "autostop_sharing"):
                    self.download_in_progress = True

                chunk_size = 102400  # 100kb

                fp = open(file_to_download, "rb")
                self.web.done = False
                canceled = False
                while not self.web.done:
                    # The user has canceled the download, so stop serving the file
                    if not self.web.stop_q.empty():
                        self.web.add_request(
                            self.web.REQUEST_CANCELED, path, {"id": history_id}
                        )
                        break

                    chunk = fp.read(chunk_size)
                    if chunk == b"":
                        self.web.done = True
                    else:
                        try:
                            yield chunk

                            # tell GUI the progress
                            downloaded_bytes = fp.tell()
                            percent = (1.0 * downloaded_bytes / self.filesize) * 100

                            # only output to stdout if running onionshare in CLI mode, or if using Linux (#203, #304)
                            if (
                                not self.web.is_gui
                                or self.common.platform == "Linux"
                                or self.common.platform == "BSD"
                            ):
                                sys.stdout.write(
                                    "\r{0:s}, {1:.2f}%          ".format(
                                        self.common.human_readable_filesize(
                                            downloaded_bytes
                                        ),
                                        percent,
                                    )
                                )
                                sys.stdout.flush()

                            self.web.add_request(
                                self.web.REQUEST_PROGRESS,
                                path,
                                {"id": history_id, "bytes": downloaded_bytes},
                            )
                            self.web.done = False
                        except:
                            # looks like the download was canceled
                            self.web.done = True
                            canceled = True

                            # tell the GUI the download has canceled
                            self.web.add_request(
                                self.web.REQUEST_CANCELED, path, {"id": history_id}
                            )

                fp.close()

                if self.common.platform != "Darwin":
                    sys.stdout.write("\n")

                # Download is finished
                if self.web.settings.get("share", "autostop_sharing"):
                    self.download_in_progress = False

                # Close the server, if necessary
                if self.web.settings.get("share", "autostop_sharing") and not canceled:
                    print("Stopped because transfer is complete")
                    self.web.running = False
                    try:
                        if shutdown_func is None:
                            raise RuntimeError("Not running with the Werkzeug Server")
                        shutdown_func()
                    except:
                        pass

            r = Response(generate())
            if use_gzip:
                r.headers.set("Content-Encoding", "gzip")
            r.headers.set("Content-Length", self.filesize)
            r.headers.set("Content-Disposition", "attachment", filename=basename)
            r = self.web.add_security_headers(r)
            # guess content type
            (content_type, _) = mimetypes.guess_type(basename, strict=False)
            if content_type is not None:
                r.headers.set("Content-Type", content_type)
            return r