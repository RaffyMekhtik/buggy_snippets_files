    def process(self):
        mailbox = self.connect_mailbox()
        emails = mailbox.messages(folder=self.parameters.folder, unread=True)

        if emails:
            for uid, message in emails:

                if (self.parameters.subject_regex and
                        not re.search(self.parameters.subject_regex,
                                      re.sub(r"\r\n\s", " ", message.subject))):
                    continue

                erroneous = False  # If errors occured this will be set to true.

                for body in message.body['plain']:
                    match = re.search(self.parameters.url_regex, str(body))
                    if match:
                        url = match.group()
                        # strip leading and trailing spaces, newlines and
                        # carriage returns
                        url = url.strip()

                        self.logger.info("Downloading report from %r.", url)
                        timeoutretries = 0
                        resp = None
                        while timeoutretries < self.http_timeout_max_tries and resp is None:
                            try:
                                resp = requests.get(url=url,
                                                    auth=self.auth, proxies=self.proxy,
                                                    headers=self.http_header,
                                                    verify=self.http_verify_cert,
                                                    cert=self.ssl_client_cert,
                                                    timeout=self.http_timeout_sec)

                            except requests.exceptions.Timeout:
                                timeoutretries += 1
                                self.logger.warn("Timeout whilst downloading the report.")

                        if resp is None and timeoutretries >= self.http_timeout_max_tries:
                            self.logger.error("Request timed out %i times in a row. " %
                                              timeoutretries)
                            erroneous = True
                            # The download timed out too often, leave the Loop.
                            continue

                        if resp.status_code // 100 != 2:
                            raise ValueError('HTTP response status code was {}.'
                                             ''.format(resp.status_code))
                        if not resp.content:
                            self.logger.warning('Got empty reponse from server.')
                        else:
                            self.logger.info("Report downloaded.")

                            template = self.new_report()

                            for report in generate_reports(template, io.BytesIO(resp.content),
                                                           self.chunk_size,
                                                           self.chunk_replicate_header):
                                self.send_message(report)

                        # Only mark read if message relevant to this instance,
                        # so other instances watching this mailbox will still
                        # check it.
                        try:
                            mailbox.mark_seen(uid)
                        except imaplib.abort:
                            # Disconnect, see https://github.com/certtools/intelmq/issues/852
                            mailbox = self.connect_mailbox()
                            mailbox.mark_seen(uid)

                if not erroneous:
                    self.logger.info("Email report read.")
                else:
                    self.logger.error("Email report read with errors, the report was not processed.")

        mailbox.logout()