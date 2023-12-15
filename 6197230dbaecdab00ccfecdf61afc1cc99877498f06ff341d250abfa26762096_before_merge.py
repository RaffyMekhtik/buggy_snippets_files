    def _format_value(self, val):
        if is_scalar(val) and missing.isna(val):
            val = self.na_rep
        elif is_float(val):
            if missing.isposinf_scalar(val):
                val = self.inf_rep
            elif missing.isneginf_scalar(val):
                val = '-{inf}'.format(inf=self.inf_rep)
            elif self.float_format is not None:
                val = float(self.float_format % val)
        return val