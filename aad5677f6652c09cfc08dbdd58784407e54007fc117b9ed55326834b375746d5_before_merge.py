    def clean_percentage(self):
        if not self.range:
            raise exceptions.ValidationError(
                _("Percentage benefits require a product range"))
        if self.value > 100:
            raise exceptions.ValidationError(
                _("Percentage discount cannot be greater than 100"))