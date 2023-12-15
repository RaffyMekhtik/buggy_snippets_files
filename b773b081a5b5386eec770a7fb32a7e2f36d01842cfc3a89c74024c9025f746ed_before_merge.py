    def build_unit(self, unit):
        try:
            converted_source = xliff_string_to_rich(unit.source)
            converted_target = xliff_string_to_rich(unit.target)
        except XMLSyntaxError:
            return super().build_unit(unit)
        output = self.storage.UnitClass("")
        output.rich_source = converted_source
        output.set_rich_target(converted_target, self.language.code)
        return output