    def _contains_display_name(self, display_name: str) -> bool:
        if not display_name:
            return False

        body = self._event.content.get("body", None)
        if not body or not isinstance(body, str):
            return False

        # Similar to _glob_matches, but do not treat display_name as a glob.
        r = regex_cache.get((display_name, False, True), None)
        if not r:
            r = re.escape(display_name)
            r = _re_word_boundary(r)
            r = re.compile(r, flags=re.IGNORECASE)
            regex_cache[(display_name, False, True)] = r

        return r.search(body)