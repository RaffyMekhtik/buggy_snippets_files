    def __setstate__(self, state):
        self._processors = [None for _ in range(len(state["_keys"]))]
        self._keymap = state["_keymap"]

        self._keys = state["_keys"]
        self.case_sensitive = state["case_sensitive"]

        if state["_translated_indexes"]:
            self._translated_indexes = state["_translated_indexes"]
            self._tuplefilter = tuplegetter(*self._translated_indexes)
        else:
            self._translated_indexes = self._tuplefilter = None