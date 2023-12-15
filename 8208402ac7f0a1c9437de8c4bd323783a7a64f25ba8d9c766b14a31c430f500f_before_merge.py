    def _verify_video_password(self, url, video_id, webpage):
        password = self._downloader.params.get('videopassword', None)
        if password is None:
            raise ExtractorError('This video is protected by a password, use the --video-password option', expected=True)
        token = self._search_regex(r'xsrft: \'(.*?)\'', webpage, 'login token')
        data = compat_urllib_parse.urlencode({
            'password': password,
            'token': token,
        })
        # I didn't manage to use the password with https
        if url.startswith('https'):
            pass_url = url.replace('https', 'http')
        else:
            pass_url = url
        password_request = compat_urllib_request.Request(pass_url + '/password', data)
        password_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        password_request.add_header('Cookie', 'xsrft=%s' % token)
        return self._download_webpage(
            password_request, video_id,
            'Verifying the password', 'Wrong password')