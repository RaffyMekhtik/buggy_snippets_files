    def first_valid_index(self):
        if len(self) == 0:
            return None

        mask = isna(self._values)
        i = mask.argmin()
        if mask[i]:
            return None
        else:
            return self.index[i]